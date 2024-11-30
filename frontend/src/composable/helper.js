import { ref, watch } from 'vue'

export function useWatchableRef(data) {
  const timeUpdateIntervalSecond = 2
  const lastUpdateText = ref('0 seconds')
  const lastUpdateMillis = ref(Date.now())

  function updateLastUpdate() {
    const differenceMillis = Date.now() - lastUpdateMillis.value
    const differenceSecond = Math.round(differenceMillis / 1000)
    if (differenceSecond < 60) {
      lastUpdateText.value = `${differenceSecond} seconds`
    } else if (60 <= differenceSecond < 3600) {
      lastUpdateText.value = `${Math.round(differenceSecond / 60)} minutes`
    } else {
      lastUpdateText.value = `${Math.round(differenceSecond / 3600)} minutes`
    }
  }

  setInterval(updateLastUpdate, timeUpdateIntervalSecond * 1000)

  watch(
    data,
    async () => {
      lastUpdateMillis.value = Date.now()
      updateLastUpdate()
    },
    { deep: true },
  )

  return { lastUpdateText }
}

import { toRaw, isRef, isReactive, isProxy } from 'vue'

export function deepToRaw(sourceObj) {
  const objectIterator = (input) => {
    if (Array.isArray(input)) {
      return input.map((item) => objectIterator(item))
    }
    if (isRef(input) || isReactive(input) || isProxy(input)) {
      return objectIterator(toRaw(input))
    }
    if (input && typeof input === 'object') {
      return Object.keys(input).reduce((acc, key) => {
        acc[key] = objectIterator(input[key])
        return acc
      }, {})
    }
    return input
  }

  return objectIterator(sourceObj)
}
