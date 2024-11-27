<script setup>
import router from '@/router';
import { GoogleAuthProvider, signInWithPopup } from 'firebase/auth'
import { useFirebaseAuth } from 'vuefire'


const auth = useFirebaseAuth()
const googleAuthProvider = new GoogleAuthProvider();
// signInAnonymously(auth).catch((reason) => {
//   console.error("Failed signinreason", reason)
// })

function onLogin() {
  signInWithPopup(auth, googleAuthProvider).catch((reason) => {
    console.error('Failed signin', reason)
  }).then(() => {
    router.push('/admin')
  })
}

</script>

<template>
  <div class="grid grid-cols-1 h-screen w-screen place-items-center">
    <button @click="onLogin()"
      class="border-2 border-black py-3 px-4 shadow-md text-2xl rounded-md hover:bg-green-50 hover:ring-4 hover:cursor-auto">
      Login
    </button>
  </div>
</template>