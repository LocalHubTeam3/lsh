import { request } from './client'

export const getTravelBasketFeedback = (locationIds, weather = []) => request('/api/ai/travel-basket-feedback', {
  method: 'POST',
  body: JSON.stringify({ location_ids: locationIds, weather }),
})
