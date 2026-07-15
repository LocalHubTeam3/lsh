const CATEGORIES = [
  { id: "12", name: "관광지", file: "서울_관광지.json", color: "#e4583e" },
  { id: "14", name: "문화시설", file: "서울_문화시설.json", color: "#6d55c7" },
  { id: "15", name: "축제·공연·행사", file: "서울_축제공연행사.json", color: "#de3d82" },
  { id: "25", name: "여행코스", file: "서울_여행코스.json", color: "#2b83d5" },
  { id: "28", name: "레포츠", file: "서울_레포츠.json", color: "#14a38b" },
  { id: "32", name: "숙박", file: "서울_숙박.json", color: "#d18d22" },
  { id: "38", name: "쇼핑", file: "서울_쇼핑.json", color: "#41615a" },
];

const map = L.map("map", { preferCanvas: true, zoomControl: false }).setView([37.5665, 126.978], 11);
L.control.zoom({ position: "bottomright" }).addTo(map);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const renderer = L.canvas({ padding: 0.5 });
const layers = new Map();
const cache = new Map();
const searchLayer = L.layerGroup().addTo(map);
const checkboxById = new Map();
const spotCount = document.querySelector("#spot-count");
const loadMessage = document.querySelector("#load-message");
const detail = document.querySelector("#place-detail");
let detailRequestId = 0;

function categoryFor(contentTypeId) {
  return CATEGORIES.find((category) => category.id === String(contentTypeId)) || {
    id: String(contentTypeId || ""),
    name: "서울 장소",
    file: "서울 관광 데이터",
    color: "#17211a",
  };
}

function placeholder(title) {
  const safe = String(title || "LocalHub").replace(/[<>&"']/g, "").slice(0, 20);
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="720" height="460">
      <rect width="100%" height="100%" fill="#e8ece9"/>
      <circle cx="360" cy="185" r="54" fill="#cad5cd"/>
      <path d="M360 145c-23 0-42 18-42 41 0 32 42 75 42 75s42-43 42-75c0-23-19-41-42-41zm0 57a17 17 0 1 1 0-34 17 17 0 0 1 0 34z" fill="#718178"/>
      <text x="50%" y="320" text-anchor="middle" fill="#536159" font-family="sans-serif" font-size="26">${safe}</text>
    </svg>`)}`;
}

async function showDetail(place, category) {
  const requestId = ++detailRequestId;
  const image = document.querySelector("#detail-image");
  image.src = place.image_url || placeholder(place.title);
  image.alt = `${place.title} 이미지`;
  image.onerror = () => { image.onerror = null; image.src = placeholder(place.title); };
  document.querySelector("#detail-type").textContent = category.name;
  document.querySelector("#detail-source").textContent = category.file;
  document.querySelector("#detail-title").textContent = place.title;
  document.querySelector("#detail-address").textContent = place.address || "주소 정보 없음";
  document.querySelector("#detail-link").href = `https://www.openstreetmap.org/?mlat=${place.latitude}&mlon=${place.longitude}#map=17/${place.latitude}/${place.longitude}`;
  const crowdStatus = document.querySelector("#crowd-status");
  crowdStatus.className = "crowd-status loading";
  crowdStatus.textContent = "실시간 혼잡도를 확인하고 있어요…";
  detail.hidden = false;
  try {
    const crowd = await window.localHubMapApi.getCrowd(place.id);
    if (requestId !== detailRequestId) return;
    if (!crowd.available) {
      crowdStatus.className = "crowd-status unavailable";
      crowdStatus.textContent = crowd.notice || "이 장소 자체의 실시간 혼잡도 데이터가 없어요.";
      return;
    }
    const population = crowd.population_estimate == null ? "인구 추정값 없음" : `약 ${crowd.population_estimate.toLocaleString("ko-KR")}명`;
    crowdStatus.className = "crowd-status available";
    crowdStatus.textContent = `현재 ${crowd.congestion_level || "정보 없음"} · ${population}`;
  } catch (error) {
    if (requestId !== detailRequestId) return;
    crowdStatus.className = "crowd-status unavailable";
    crowdStatus.textContent = error.status === 503
      ? "서울시 API 키를 적어야 해요. backend/.env의 SEOUL_API_KEY를 설정해 주세요."
      : "혼잡도 정보를 불러오지 못했어요.";
  }
}

function createLayer(items, category) {
  const group = L.layerGroup();
  items.forEach((place) => {
    const spot = L.circleMarker([place.latitude, place.longitude], {
      renderer,
      radius: 5,
      weight: 1.5,
      color: "#fff",
      fillColor: category.color,
      fillOpacity: 0.88,
    });
    spot.on("click", () => showDetail(place, category));
    spot.addTo(group);
  });
  return group;
}

function updateSpotCount() {
  let total = 0;
  layers.forEach((layer, id) => {
    if (map.hasLayer(layer)) total += cache.get(id)?.total || 0;
  });
  spotCount.textContent = `${total.toLocaleString("ko-KR")}개 spot`;
}

function setMessage(message = "") {
  loadMessage.textContent = message;
  loadMessage.hidden = !message;
}

async function enableCategory(category) {
  const checkbox = checkboxById.get(category.id);
  checkbox.disabled = true;
  setMessage(`${category.file}을 불러오는 중입니다.`);
  try {
    if (!cache.has(category.id)) {
      cache.set(category.id, await window.localHubMapApi.getLocations(category.id));
    }
    if (!layers.has(category.id)) {
      layers.set(category.id, createLayer(cache.get(category.id).items, category));
    }
    if (checkbox.checked) layers.get(category.id).addTo(map);
    checkbox.closest("label").querySelector(".count").textContent = `${cache.get(category.id).total.toLocaleString("ko-KR")}개`;
  } catch (error) {
    checkbox.checked = false;
    setMessage(`${category.name}: ${error.message}`);
    return;
  } finally {
    checkbox.disabled = false;
  }
  setMessage();
  updateSpotCount();
}

function disableCategory(category) {
  const layer = layers.get(category.id);
  if (layer) map.removeLayer(layer);
  updateSpotCount();
}

function buildCategoryControls() {
  const container = document.querySelector("#category-list");
  CATEGORIES.forEach((category, index) => {
    const label = document.createElement("label");
    label.className = "category-option";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = category.id;
    checkbox.checked = index === 0;
    checkboxById.set(category.id, checkbox);

    const color = document.createElement("span");
    color.className = "color-dot";
    color.style.backgroundColor = category.color;
    const text = document.createElement("span");
    text.className = "category-text";
    const name = document.createElement("strong");
    name.textContent = category.name;
    const file = document.createElement("small");
    file.textContent = category.file;
    text.append(name, file);
    const count = document.createElement("span");
    count.className = "count";
    count.textContent = "";
    label.append(checkbox, color, text, count);
    container.append(label);

    checkbox.addEventListener("change", () => checkbox.checked ? enableCategory(category) : disableCategory(category));
  });
}

document.querySelector("#toggle-all").addEventListener("click", async (event) => {
  const shouldSelect = CATEGORIES.some((item) => !checkboxById.get(item.id).checked);
  event.currentTarget.textContent = shouldSelect ? "전체 해제" : "전체 선택";
  for (const category of CATEGORIES) {
    const checkbox = checkboxById.get(category.id);
    if (checkbox.checked === shouldSelect) continue;
    checkbox.checked = shouldSelect;
    if (shouldSelect) await enableCategory(category);
    else disableCategory(category);
  }
});

document.querySelector("#detail-close").addEventListener("click", () => { detail.hidden = true; });

const searchForm = document.querySelector("#map-search-form");
const searchInput = document.querySelector("#map-search-input");
const searchResults = document.querySelector("#map-search-results");
const searchClear = document.querySelector("#map-search-clear");

function clearSearch() {
  searchLayer.clearLayers();
  searchResults.replaceChildren();
  searchResults.hidden = true;
  searchClear.hidden = true;
  searchInput.value = "";
}

function openSearchPlace(place) {
  map.flyTo([place.latitude, place.longitude], 16, { duration: 0.7 });
  showDetail(place, categoryFor(place.content_type_id));
}

function renderSearchResults(data) {
  searchResults.replaceChildren();
  const heading = document.createElement("p");
  heading.className = "search-result-heading";
  heading.textContent = data.total > data.items.length
    ? `총 ${data.total.toLocaleString("ko-KR")}개 중 ${data.items.length}개 표시`
    : `총 ${data.total.toLocaleString("ko-KR")}개 장소`;
  searchResults.append(heading);
  if (!data.items.length) {
    const empty = document.createElement("p");
    empty.className = "search-empty";
    empty.textContent = "이름에 검색어가 포함된 장소가 없어요.";
    searchResults.append(empty);
    searchResults.hidden = false;
    return;
  }
  data.items.forEach((place) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "search-result-item";
    const title = document.createElement("strong");
    title.textContent = place.title;
    const meta = document.createElement("span");
    meta.textContent = `${categoryFor(place.content_type_id).name} · ${place.address || "주소 정보 없음"}`;
    button.append(title, meta);
    button.addEventListener("click", () => openSearchPlace(place));
    searchResults.append(button);
  });
  searchResults.hidden = false;
}

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = searchInput.value.trim();
  if (!query) { clearSearch(); return; }
  searchClear.hidden = false;
  searchResults.hidden = false;
  searchResults.textContent = "검색 중이에요…";
  searchLayer.clearLayers();
  try {
    const data = await window.localHubMapApi.searchLocations(query);
    data.items.forEach((place) => {
      const category = categoryFor(place.content_type_id);
      L.circleMarker([place.latitude, place.longitude], {
        renderer,
        radius: 8,
        weight: 3,
        color: "#ffffff",
        fillColor: category.color,
        fillOpacity: 1,
      }).on("click", () => openSearchPlace(place)).addTo(searchLayer);
    });
    renderSearchResults(data);
    if (data.items.length === 1) openSearchPlace(data.items[0]);
    else if (data.items.length > 1) {
      const bounds = L.latLngBounds(data.items.map((place) => [place.latitude, place.longitude]));
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }
  } catch (error) {
    searchResults.textContent = `${error.message}. Backend 서버를 확인해 주세요.`;
  }
});

searchClear.addEventListener("click", clearSearch);
buildCategoryControls();
enableCategory(CATEGORIES[0]);
