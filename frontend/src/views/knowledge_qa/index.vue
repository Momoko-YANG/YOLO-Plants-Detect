<template>
  <div class="streamlit-fullscreen-container">
    <!-- 全屏嵌入Streamlit应用 -->
    <iframe
      :src="streamlitUrl"
      class="fullscreen-iframe"
      frameborder="0"
      scrolling="auto"
    ></iframe>
  </div>
</template>

<script setup lang="ts" name="plantChat">
import { ref } from 'vue';

// Streamlit应用地址（需与实际启动的Streamlit端口一致）
const streamlitUrl = ref('http://localhost:8501');
</script>

<style scoped lang="scss">
/* 根容器：清除所有默认边距和内边距，铺满视口 */
.streamlit-fullscreen-container {
  width: 100vw; /* 视口宽度100% */
  height: 100vh; /* 视口高度100% */
  margin: 0;
  padding: 0;
  overflow: hidden; /* 隐藏滚动条，避免整体页面滚动 */
}

/* iframe：完全铺满根容器，无任何边距和样式限制 */
.fullscreen-iframe {
  width: 100%;
  height: 100%;
  border: none; /* 彻底移除边框 */
  margin: 0;
  padding: 0;
}

/* 清除可能存在的全局默认样式影响 */
:deep(body) {
  margin: 0;
  padding: 0;
  overflow: hidden;
}
</style>