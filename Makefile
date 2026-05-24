REMOTE := deployacc@fsn-web02.cyberbits.org
AGGREGATOR := defcon-news-aggregator
API := defcon-api-gateway

# Full production deploy: build + push containers, then rescore + flush cache
.PHONY: deploy
deploy: tofu-apply prd-rescore

# OpenTofu apply (builds images on remote, restarts containers)
.PHONY: tofu-apply
tofu-apply:
	cd tofu && tofu apply -auto-approve

# Rescore existing articles + flush API cache on production
# Run this after any change to scoring logic (triggers.py, vocabulary.py, scoring.py)
.PHONY: prd-rescore
prd-rescore:
	@echo "→ Backfilling article scores on PRD..."
	ssh $(REMOTE) "docker exec $(AGGREGATOR) python -m scripts.backfill_article_scores"
	@echo "→ Flushing API cache on PRD..."
	$(eval PRD_SECRET := $(shell ssh $(REMOTE) "docker inspect $(API) --format '{{range .Config.Env}}{{println .}}{{end}}' | grep INTERNAL_SECRET | cut -d= -f2"))
	ssh $(REMOTE) 'docker exec $(API) node -e " \
		const http = require(\"http\"); \
		const req = http.request({host:\"localhost\",port:4000,path:\"/internal/cache/invalidate\",method:\"POST\",headers:{\"X-Internal-Token\":\"$(PRD_SECRET)\"}}, \
			r => { let d=\"\"; r.on(\"data\",c=>d+=c); r.on(\"end\",()=>console.log(d)); }); \
		req.end();"'
	@echo "→ Done. PRD scores updated."

# Run tests locally (scoring pipeline only — requires .venv)
.PHONY: test
test:
	cd services/news-aggregator && .venv/bin/pytest tests/test_triggers.py tests/test_vocabulary.py tests/test_scoring.py -v

# Run full test suite locally
.PHONY: test-all
test-all:
	cd services/news-aggregator && .venv/bin/pytest -v
