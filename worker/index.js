const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "https://ko-72.com",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}

async function resendRequest(env, path, method = "GET", body = null) {
  const opts = {
    method,
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`https://api.resend.com${path}`, opts);
  return res.json();
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }

    const url = new URL(request.url);

    // POST /subscribe — add email to Resend audience
    if (url.pathname === "/subscribe" && request.method === "POST") {
      let email;
      try {
        ({ email } = await request.json());
      } catch {
        return json({ error: "Invalid JSON" }, 400);
      }
      if (!email || !email.includes("@")) {
        return json({ error: "Invalid email" }, 400);
      }
      await resendRequest(env, `/audiences/${env.RESEND_AUDIENCE_ID}/contacts`, "POST", { email });
      return json({ ok: true });
    }

    // POST /unsubscribe — remove email from Resend audience
    if (url.pathname === "/unsubscribe" && request.method === "POST") {
      let email;
      try {
        ({ email } = await request.json());
      } catch {
        return json({ error: "Invalid JSON" }, 400);
      }
      // Look up contact by listing audience and finding by email
      const contacts = await resendRequest(env, `/audiences/${env.RESEND_AUDIENCE_ID}/contacts`);
      const contact = (contacts.data ?? []).find((c) => c.email === email);
      if (contact) {
        await resendRequest(
          env,
          `/audiences/${env.RESEND_AUDIENCE_ID}/contacts/${contact.id}`,
          "DELETE"
        );
      }
      return json({ ok: true });
    }

    return json({ error: "Not found" }, 404);
  },
};
