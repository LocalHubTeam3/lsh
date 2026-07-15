const TYPE_NAMES = {
  12: "관광지",
  14: "문화시설",
  15: "축제·공연",
  25: "여행코스",
  28: "레포츠",
  32: "숙박",
  38: "쇼핑",
};

const state = { search: "", contentType: "", page: 1, size: 12, total: 0 };
const grid = document.querySelector("#place-grid");
const statusBox = document.querySelector("#status");
const resultCount = document.querySelector("#result-count");
const pageLabel = document.querySelector("#page-label");
const prevButton = document.querySelector("#prev-button");
const nextButton = document.querySelector("#next-button");

const escapeHtml = (value) => {
  const element = document.createElement("div");
  element.textContent = value ?? "";
  return element.innerHTML;
};

const placeholder = (title) => {
  const safeTitle = escapeHtml(title).slice(0, 24);
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="720" height="480">
      <rect width="100%" height="100%" fill="#e9ece7"/>
      <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle"
        fill="#617064" font-family="sans-serif" font-size="28">${safeTitle}</text>
    </svg>`)}`;
};

function renderCard(place) {
  const article = document.createElement("article");
  article.className = "place-card";
  const image = place.image_url || placeholder(place.title);
  const address = [place.address, place.address_detail].filter(Boolean).join(" ") || "주소 정보 없음";
  const type = TYPE_NAMES[place.content_type_id] || "서울 장소";
  const mapLink = place.latitude != null && place.longitude != null
    ? `https://www.openstreetmap.org/?mlat=${place.latitude}&mlon=${place.longitude}#map=16/${place.latitude}/${place.longitude}`
    : "";

  article.innerHTML = `
    <div class="card-image-wrap">
      <img class="card-image" src="${escapeHtml(image)}" alt="${escapeHtml(place.title)}" loading="lazy" referrerpolicy="no-referrer" />
      <span class="type-badge">${escapeHtml(type)}</span>
    </div>
    <div class="card-body">
      <h3>${escapeHtml(place.title)}</h3>
      <p>${escapeHtml(address)}</p>
      ${mapLink ? `<a href="${mapLink}" target="_blank" rel="noreferrer">지도에서 보기 <span>↗</span></a>` : ""}
    </div>`;
  const imageElement = article.querySelector("img");
  imageElement.addEventListener("error", () => {
    imageElement.src = placeholder(place.title);
  }, { once: true });
  return article;
}

function setLoading(isLoading) {
  grid.classList.toggle("loading", isLoading);
  prevButton.disabled = isLoading;
  nextButton.disabled = isLoading;
}

async function loadPlaces() {
  setLoading(true);
  statusBox.hidden = true;
  try {
    const data = await window.localHubApi.getLocations(state);
    state.total = data.total;
    const totalPages = Math.max(1, Math.ceil(data.total / state.size));
    grid.replaceChildren(...data.items.map(renderCard));
    resultCount.textContent = `총 ${data.total.toLocaleString("ko-KR")}개의 장소`;
    pageLabel.textContent = `${data.page} / ${totalPages}`;
    prevButton.disabled = data.page <= 1;
    nextButton.disabled = data.page >= totalPages;
    if (!data.items.length) {
      statusBox.textContent = "조건에 맞는 장소가 없습니다. 다른 검색어를 입력해 보세요.";
      statusBox.hidden = false;
    }
  } catch (error) {
    grid.replaceChildren();
    resultCount.textContent = "불러오기 실패";
    statusBox.textContent = `${error.message}. FastAPI 서버와 API 주소를 확인해 주세요.`;
    statusBox.hidden = false;
  } finally {
    setLoading(false);
  }
}

document.querySelector("#search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  state.search = document.querySelector("#search-input").value;
  state.contentType = document.querySelector("#type-select").value;
  state.page = 1;
  loadPlaces();
});

prevButton.addEventListener("click", () => {
  if (state.page > 1) { state.page -= 1; loadPlaces(); window.scrollTo({ top: 420, behavior: "smooth" }); }
});
nextButton.addEventListener("click", () => {
  if (state.page * state.size < state.total) { state.page += 1; loadPlaces(); window.scrollTo({ top: 420, behavior: "smooth" }); }
});

loadPlaces();
