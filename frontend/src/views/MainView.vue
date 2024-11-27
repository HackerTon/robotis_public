<script setup>
import CustomList from '@/components/CustomList.vue';
import { db } from '@/main';
import { collection, orderBy, query, getDocs, deleteDoc } from 'firebase/firestore';
import { useCollection, useFirebaseAuth } from 'vuefire';

import { useWatchableRef } from '@/composable/helper';
import { useWebsocket } from '@/composable/websocket';
import router from '@/router/index';

const auth = useFirebaseAuth()

// Live scoreboard
const scoreBoardCollection = useCollection(query(collection(db, 'scores'), orderBy('score', 'desc')), { ssrKey: 'something' });
const { lastUpdateText: scoreboardLastUpdate } = useWatchableRef(scoreBoardCollection)

// Websocket
const { isSocketOpen } = useWebsocket('ws://localhost:8000/ws')

// Button callback
async function onSignout() {
  auth.signOut().then(() => router.push('/'))
}
async function onClearScores() {


  const documents = await getDocs(collection(db, 'scores'));
  documents.forEach(async (document) => {
    await deleteDoc(document.ref)
  })
}
</script>

<template>
  <div class="flex flex-col h-screen">
    <p class="flex-none grid place-content-center p-5 text-5xl font-semibold bg-yellow-100">
      2024 Competition Admin Panel
    </p>
    <div class="flex-1 grid grid-cols-1 md:grid-cols-2 m-5 gap-5">
      <!-- COL 1 -->
      <div class="flex-1 flex flex-col border-black border-2 rounded-lg">
        <div class="text-center mx-5 mb-2 p-3 font-bold text-2xl">Ranking List</div>
        <CustomList :data="scoreBoardCollection" :text="scoreboardLastUpdate" />
      </div>

      <!-- COL 2 -->
      <div class=" flex-1 flex flex-col border-black border-2 rounded-lg">
        <div class="grid grix-row-2 gap-2.5 p-5">
          <p v-if="isSocketOpen">Websocket status: {{ isSocketOpen ? 'OPENED' : 'DISCONNECTED' }}
          </p>
          <p class="text-red-600" v-else>Websocket status: {{ isSocketOpen ? 'OPENED' :
            'DISCONNECTED' }}
          </p>
          <div class="grid grid-cols-2 gap-2.5">
            <button @click="onClearScores"
              class="border-2 border-black py-3 px-4 shadow-md text-base rounded-md hover:bg-red-500 hover:ring-4 hover:cursor-auto">
              CLEAR SCORE
            </button>
            <button @click="onSignout"
              class="border-2 border-black py-3 px-4 shadow-md text-base rounded-md hover:bg-red-500 hover:ring-4 hover:cursor-auto">
              SIGNOUT
            </button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>