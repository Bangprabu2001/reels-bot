// Penerima pesan Telegram (Cloudflare Worker, gratis) untuk pabrik KUIS. Menjawab tombol SEKETIKA,
// dan hanya menyalakan pabrik di GitHub Actions saat ada pekerjaan berat.
//
// Variabel yang harus diisi di Cloudflare (Settings -> Variables and Secrets):
//   TELEGRAM_BOT_TOKEN  (Secret)  token dari BotFather
//   GITHUB_TOKEN        (Secret)  token GitHub dengan izin Actions: Read and write
//   WEBHOOK_SECRET      (Secret)  kata sandi bebas (huruf/angka/_/-), dipakai juga saat setWebhook
//   GITHUB_REPO         (Text)    contoh: usernamekamu/reels-bot
//   OWNER_CHAT_ID       (Text)    angka Chat ID kamu (kosongkan dulu untuk mengetahuinya lewat /start)
//   GITHUB_BRANCH       (Text, opsional) default: main

const MENU = {
  inline_keyboard: [
    [{ text: "🎯 Buat 1 video kuis", callback_data: "b:1" }],
    [{ text: "🎯🎯🎯 Buat 3 video kuis", callback_data: "b:3" }],
    [{ text: "📋 Status", callback_data: "status" }, { text: "🛑 Hentikan", callback_data: "stop" }],
  ],
};
const KEYBOARD_TETAP = { keyboard: [[{ text: "🏭 MENU" }]], resize_keyboard: true, is_persistent: true };

async function tg(env, method, body) {
  const r = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  return r.json().catch(() => ({}));
}
const kirim = (env, chat, text, markup) =>
  tg(env, "sendMessage", { chat_id: chat, text, ...(markup ? { reply_markup: markup } : {}) });

function gh(env, path, method = "GET", body) {
  return fetch(`https://api.github.com/repos/${env.GITHUB_REPO}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "pabrik-konten-worker",
      "X-GitHub-Api-Version": "2022-11-28",
      "content-type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
}

async function nyalakan(env, chat, aksi, data) {
  const r = await gh(env, "/actions/workflows/pabrik.yml/dispatches", "POST", {
    ref: env.GITHUB_BRANCH || "main",
    inputs: { aksi, data: String(data), chat: String(chat) },
  });
  if (r.status !== 204) {
    const t = await r.text();
    await kirim(env, chat, `❌ Gagal menyalakan pabrik (GitHub ${r.status}).\n${t.slice(0, 250)}\n\nPeriksa GITHUB_TOKEN, GITHUB_REPO, dan nama file workflow pabrik.yml.`, MENU);
    return false;
  }
  return true;
}

async function status(env, chat) {
  const r = await gh(env, "/actions/runs?per_page=6");
  if (!r.ok) return kirim(env, chat, `Tidak bisa membaca status (GitHub ${r.status}).`, MENU);
  const j = await r.json();
  const baris = (j.workflow_runs || []).map((x) => {
    const s = x.status === "completed" ? (x.conclusion === "success" ? "✅ selesai" : `❌ ${x.conclusion}`) :
      x.status === "queued" ? "⏳ antre" : "⚙️ sedang jalan";
    return `#${x.run_number} ${s}`;
  });
  const jalan = (j.workflow_runs || []).filter((x) => x.status !== "completed").length;
  return kirim(env, chat, (jalan ? `Pabrik sedang bekerja (${jalan} proses).\n` : "Pabrik sedang menganggur.\n") + baris.join("\n"), MENU);
}

async function hentikan(env, chat) {
  const r = await gh(env, "/actions/runs?per_page=10");
  const j = r.ok ? await r.json() : { workflow_runs: [] };
  let n = 0;
  for (const x of j.workflow_runs || []) {
    if (x.status === "in_progress" || x.status === "queued") {
      await gh(env, `/actions/runs/${x.id}/cancel`, "POST");
      n++;
    }
  }
  return kirim(env, chat, n ? `🛑 ${n} proses dihentikan.` : "Tidak ada proses yang sedang berjalan.", MENU);
}

async function tangani(upd, env) {
  const owner = String(env.OWNER_CHAT_ID || "").trim();

  if (upd.callback_query) {
    const cq = upd.callback_query;
    const chat = String(cq.message.chat.id);
    if (!owner || chat !== owner) return;
    const [aksi, ...sisa] = String(cq.data || "").split(":");
    const arg = sisa.join(":");
    const jawab = (text) => tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text });
    const hapusTombol = () =>
      tg(env, "editMessageReplyMarkup", { chat_id: chat, message_id: cq.message.message_id, reply_markup: { inline_keyboard: [] } });

    if (aksi === "b") {
      await jawab("Pabrik dinyalakan...");
      const n = arg === "3" ? 3 : 1;
      if (await nyalakan(env, chat, "buat", String(n)))
        await kirim(env, chat, `⏳ Diterima. Membuat ${n} video kuis, sekitar 8 menit per video. Aku kabari otomatis.`);
    } else if (aksi === "ok" || aksi === "re" || aksi === "no") {
      await jawab("Diproses...");
      await hapusTombol();
      if (await nyalakan(env, chat, aksi, arg)) {
        if (aksi !== "ok") await kirim(env, chat, "⏳ Diterima, membuat soal baru (±8 menit).");
      }
    } else if (aksi === "cap") {
      await jawab("Ketik revisinya");
      await tg(env, "sendMessage", {
        chat_id: chat,
        text: `✏️ Balas (reply) pesan ini dengan instruksi revisi caption.\nContoh: lebih singkat / tambah ajakan komentar / hapus emoji\n[#${arg}]`,
        reply_markup: { force_reply: true, input_field_placeholder: "contoh: lebih singkat" },
      });
    } else if (aksi === "status") {
      await jawab("");
      await status(env, chat);
    } else if (aksi === "stop") {
      await jawab("");
      await hentikan(env, chat);
    }
    return;
  }

  const m = upd.message;
  if (!m) return;
  const chat = String(m.chat.id);
  const teks = (m.text || "").trim();

  if (!owner) {
    if (teks.startsWith("/start"))
      await kirim(env, chat, `Chat ID kamu: ${chat}\nIsi angka ini ke variabel OWNER_CHAT_ID di Cloudflare, lalu kirim /start lagi.`);
    return;
  }
  if (chat !== owner) return; // bot pribadi: abaikan orang lain

  // balasan untuk revisi caption: pesan yang di-reply memuat [#job]
  const rep = m.reply_to_message && m.reply_to_message.text;
  const mj = rep && rep.match(/\[#(\d+)\]/);
  if (mj && teks) {
    await kirim(env, chat, "⏳ Merevisi caption...");
    await nyalakan(env, chat, "caption", `${mj[1]}|${teks}`);
    return;
  }

  if (teks.startsWith("/start")) {
    await kirim(env, chat, "Halo! Pabrik kuis siap. Tekan tombol 🏭 MENU di bawah kapan saja.", KEYBOARD_TETAP);
  }
  await kirim(env, chat, "Pilih yang mau dibuat:", MENU);
}

export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") return new Response("Pabrik Konten aktif ✅");
    if (env.WEBHOOK_SECRET && request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.WEBHOOK_SECRET)
      return new Response("forbidden", { status: 403 });
    let upd;
    try { upd = await request.json(); } catch { return new Response("bad request", { status: 400 }); }
    ctx.waitUntil(tangani(upd, env).catch(() => {}));
    return new Response("ok");
  },
};
