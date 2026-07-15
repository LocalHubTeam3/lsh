export const LOCATION_TYPES = [
  { id: '12', name: '관광지', color: '#267D78', symbol: '명' },
  { id: '14', name: '문화시설', color: '#765A98', symbol: '문' },
  { id: '15', name: '축제·행사', color: '#D8A43A', symbol: '축' },
  { id: '25', name: '여행코스', color: '#3973A5', symbol: '길' },
  { id: '28', name: '레포츠', color: '#3973A5', symbol: '활' },
  { id: '32', name: '숙박', color: '#8B654E', symbol: '숙' },
  { id: '38', name: '쇼핑', color: '#C6544F', symbol: '장' },
]

export function locationType(id) {
  return LOCATION_TYPES.find((item) => item.id === String(id)) || { id: '', name: '서울 장소', color: '#267D78', symbol: '곳' }
}
