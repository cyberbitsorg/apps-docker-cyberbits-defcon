const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export async function login(password: string): Promise<string> {
  const response = await fetch(`${BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ error: "Login failed" }));
    throw new Error(err.error || "Login failed");
  }

  const { token } = await response.json();
  return token;
}
