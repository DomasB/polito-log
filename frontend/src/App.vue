<script setup lang="ts">
import { NConfigProvider } from 'naive-ui'
import StatementExample from '@/components/StatementExample.vue';
import { darkTheme } from 'naive-ui'
</script>

<template>
  <n-config-provider :theme="darkTheme">
    <StatementExample />
  </n-config-provider>
</template>

<style>
body {
  margin: 0;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #121212;
  height: 100vh;
}
</style>
