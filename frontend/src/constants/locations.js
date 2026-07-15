export const LOCATION_TYPES = [
  { id: '12', name: '관광지', color: '#e84f3d' },
  { id: '14', name: '문화시설', color: '#7259c7' },
  { id: '15', name: '축제·행사', color: '#db3e7d' },
  { id: '25', name: '여행코스', color: '#2678c9' },
  { id: '28', name: '레포츠', color: '#07947d' },
  { id: '32', name: '숙박', color: '#c27a12' },
  { id: '38', name: '쇼핑', color: '#42665d' },
]

export function locationType(id) {
  return LOCATION_TYPES.find((item) => item.id === String(id)) || { id: '', name: '서울 장소', color: '#42665d' }
}
