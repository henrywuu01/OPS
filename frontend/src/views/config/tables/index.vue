<template>
  <div class="page-container">
    <a-card :title="title">
      <a-empty description="功能开发中 - M4 实现" />
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const title = ref('配置表管理')
</script>

<style scoped>
.page-container {
  padding: 16px;
}
</style>
