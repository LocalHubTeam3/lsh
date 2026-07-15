(() => {
  const API_BASE_URL = window.LOCALHUB_API_BASE_URL || "http://localhost:8000";
  const history = [];
  const root = document.createElement("div");
  root.innerHTML = `
    <button class="lh-chat-launcher" type="button" aria-label="여행 챗봇 열기">✦</button>
    <section class="lh-chat-panel" aria-label="LocalHub 여행 챗봇" hidden>
      <header class="lh-chat-header">
        <div><strong>LocalHub 여행 도우미</strong><span>SQLite 장소 데이터 기반 답변</span></div>
        <button class="lh-chat-close" type="button" aria-label="챗봇 닫기">×</button>
      </header>
      <div class="lh-chat-messages" aria-live="polite"></div>
      <form class="lh-chat-form">
        <input class="lh-chat-input" maxlength="2000" placeholder="서울 장소를 물어보세요" aria-label="챗봇 질문" />
        <button class="lh-chat-send" type="submit">전송</button>
      </form>
    </section>`;
  document.body.append(root);

  const launcher = root.querySelector(".lh-chat-launcher");
  const panel = root.querySelector(".lh-chat-panel");
  const close = root.querySelector(".lh-chat-close");
  const messages = root.querySelector(".lh-chat-messages");
  const form = root.querySelector(".lh-chat-form");
  const input = root.querySelector(".lh-chat-input");
  const send = root.querySelector(".lh-chat-send");

  function addMessage(text, role = "bot", notice = false) {
    const message = document.createElement("div");
    message.className = `lh-chat-message ${role}${notice ? " notice" : ""}`;
    message.textContent = text;
    messages.append(message);
    messages.scrollTop = messages.scrollHeight;
  }

  function disableChat() {
    input.disabled = true;
    send.disabled = true;
    input.placeholder = "OPENAI_API_KEY 설정 필요";
  }

  async function initialize() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/features`, { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error("기능 상태를 확인하지 못했습니다.");
      const features = await response.json();
      if (!features.openai_api_configured) {
        addMessage("OpenAI API 키를 적어야 해요. backend/.env의 OPENAI_API_KEY를 설정한 뒤 서버를 다시 실행해 주세요.", "bot", true);
        disableChat();
        return;
      }
      addMessage("안녕하세요! 서울의 장소와 여행 코스를 물어보세요.");
    } catch (error) {
      addMessage(`${error.message} FastAPI 서버 주소를 확인해 주세요.`, "bot", true);
    }
  }

  launcher.addEventListener("click", () => { panel.hidden = !panel.hidden; if (!panel.hidden) input.focus(); });
  close.addEventListener("click", () => { panel.hidden = true; });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text || input.disabled) return;
    addMessage(text, "user");
    input.value = "";
    input.disabled = true;
    send.disabled = true;
    const waiting = document.createElement("div");
    waiting.className = "lh-chat-message bot";
    waiting.textContent = "답변을 만들고 있어요…";
    messages.append(waiting);
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ message: text, history: history.slice(-6) }),
      });
      const body = await response.json().catch(() => ({}));
      waiting.remove();
      if (!response.ok) {
        const detail = response.status === 503 ? "OpenAI API 키를 적어야 해요." : (body.detail || "챗봇 답변을 불러오지 못했어요.");
        addMessage(detail, "bot", true);
        if (response.status === 503) { disableChat(); return; }
      } else {
        addMessage(body.answer);
        history.push({ role: "user", content: text }, { role: "assistant", content: body.answer });
      }
    } catch (_) {
      waiting.remove();
      addMessage("챗봇 API에 연결할 수 없어요. FastAPI 서버를 확인해 주세요.", "bot", true);
    } finally {
      if (!send.disabled || input.placeholder !== "OPENAI_API_KEY 설정 필요") {
        input.disabled = false;
        send.disabled = false;
        input.focus();
      }
    }
  });
  initialize();
})();
