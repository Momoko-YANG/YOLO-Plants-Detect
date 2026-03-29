<template>
  <div class="system-predict-container layout-padding">
    <div class="system-predict-padding layout-padding-auto layout-padding-view">
      <!-- 顶部控制区域 -->
      <div class="header">
        <div class="weight">
          <el-select v-model="kind" placeholder="请选择识别类别" size="large" style="width: 200px" @change="getData">
            <el-option v-for="item in state.kind_items" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <div class="weight">
          <el-select v-model="weight" placeholder="请选择模型" size="large" style="margin-left: 20px;width: 200px">
            <el-option v-for="item in state.weight_items" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <div class="conf" style="margin-left: 20px;display: flex; flex-direction: row;">
          <div style="font-size: 14px;margin-right: 20px;display: flex;justify-content: start;align-items: center;color: #909399;">
            设置最小置信度阈值
          </div>
          <el-slider 
            v-model="conf" 
            :format-tooltip="formatTooltip" 
            style="width: 300px;" 
            :min="0" 
            :max="100" 
            :step="1"
          />
        </div>
        <div class="button-section" style="margin-left: 20px">
          <el-button type="primary" @click="upData" class="predict-button">开始预测</el-button>
        </div>
      </div>

      <!-- 上部分：三列布局（原图片+预测后图片+AI建议） -->
      <div class="upper-section">
        <!-- 第一列：原图片（修复上传功能） -->
        <div class="upper-column">
          <el-card shadow="hover" class="image-card">
            <div class="card-header">
              原图片
              <!-- 添加"更换图片"按钮，提供明确的重新上传入口 -->
              <el-button 
                v-if="imageUrl" 
                type="text" 
                size="small" 
                class="change-image-btn"
                @click="handleChangeImage"
              >
                更换图片
              </el-button>
            </div>
            <div class="image-container">
              <!-- 核心修复：上传组件始终包裹图片，保持可点击性 -->
              <el-upload 
                ref="uploadFile" 
                class="avatar-uploader"
                action="http://localhost:9999/files/upload" 
                :show-file-list="false"
                :on-success="handleAvatarSuccessone"
              >
                <img v-if="imageUrl" :src="imageUrl" class="avatar" />
                <div v-else class="avatar-uploader-icon">
                  <span>点击上传图片</span>
                </div>
              </el-upload>
            </div>
          </el-card>
        </div>

        <!-- 第二列：预测后图片 -->
        <div class="upper-column">
          <el-card shadow="hover" class="image-card">
            <div class="card-header">预测结果</div>
            <div class="image-container">
              <img v-if="predictedImageUrl" :src="predictedImageUrl" class="avatar" />
              <div v-else class="empty-image">预测后将显示结果图片</div>
            </div>
          </el-card>
        </div>

        <!-- 第三列：AI建议 -->
        <div class="upper-column">
          <el-card shadow="hover" class="suggestion-card">
            <div class="card-header">AI建议</div>
            <div class="suggestion-content">
              <template v-if="state.aiSuggestion.loading">
                <div class="loading">加载中...</div>
              </template>
              <template v-else-if="state.aiSuggestion.content">
                <div v-html="state.aiSuggestion.content"></div>
              </template>
              <template v-else>
                <div class="empty-image">完成识别后将显示AI建议</div>
              </template>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 下部分：一行布局（识别结果+预测概率+识别时间） -->
      <div class="lower-section">
        <el-card shadow="hover" class="result-card">
          <div class="result-content">
            <div class="result-item">
              <span class="result-icon">🏷️</span>
              <span class="result-label">类别：</span>
              <span class="result-value">{{ formatLabel(state.predictionResult.label) }}</span>
            </div>
            <div class="result-item">
              <span class="result-icon">📊</span>
              <span class="result-label">预测概率：</span>
              <span class="result-value">{{ state.predictionResult.confidence || '——' }}</span>
            </div>
            <div class="result-item">
              <span class="result-icon">⏱️</span>
              <span class="result-label">识别时间：</span>
              <span class="result-value">{{ state.predictionResult.allTime || '——' }}</span>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="personal">
import { reactive, ref, onMounted, watch } from 'vue';
import type { UploadInstance, UploadProps } from 'element-plus';

import { ElMessage } from 'element-plus';
import request from '/@/utils/request';
import { useUserInfo } from '/@/stores/userInfo';
import { storeToRefs } from 'pinia';
import { formatDate } from '/@/utils/formatTime';
import kindConfig from '/@/config/kindConfig.json';

// 响应式变量
const imageUrl = ref('');
const predictedImageUrl = ref(''); // 预测后图片地址
const conf = ref(1);
const weight = ref('');
const kind = ref('');
const uploadFile = ref<UploadInstance>();
const stores = useUserInfo();
const { userInfos } = storeToRefs(stores);
const isUserInfoLoaded = ref(false);

const state = reactive({
  weight_items: [] as { value: string; label: string }[],
  kind_items: kindConfig.kind_items,
  img: '',
  predictionResult: {
    label: '',
    confidence: '',
    allTime: '',
  },
  aiSuggestion: {
    content: '',
    loading: false
  },
  form: {
    username: '',
    inputImg: null as any,
    weight: '',
    conf: null as any,
    kind: '',
    startTime: ''
  },
});

// 格式化滑块显示
const formatTooltip = (val: number) => {
  return val / 100;
};

// 手动触发上传（用于"更换图片"按钮）
const handleChangeImage = () => {
  if (uploadFile.value) {
    // 重置图片地址，避免视觉混淆
    imageUrl.value = '';
    // 手动触发上传组件的点击事件
    uploadFile.value.$refs.input.click();
  }
};

// 处理图片上传成功（修复：移除v-model绑定，避免状态冲突）
const handleAvatarSuccessone: UploadProps['onSuccess'] = (response, uploadFile) => {
  if (uploadFile.raw) {
    // 释放旧的URL对象，避免内存泄漏
    if (imageUrl.value) {
      URL.revokeObjectURL(imageUrl.value);
    }
    // 创建新的URL
    imageUrl.value = URL.createObjectURL(uploadFile.raw);
    state.img = response.data;
    predictedImageUrl.value = ''; // 重置预测结果
    ElMessage.success('图片上传成功');
  }
};

// 获取模型列表
const getData = () => {
  console.log('触发模型列表加载，当前类别：', kind.value);
  state.weight_items = [];
  
  if (!kind.value) {
    ElMessage.warning('请先选择识别类别');
    return;
  }

  request.get('/api/flask/file_names', { timeout: 10000 })
    .then((res) => {
      console.log('接口原始响应：', res);
      if (res.code !== '0') {
        ElMessage.error(`接口错误：${res.msg || '未知错误'}`);
        return;
      }

      let dataObj: any;
      try {
        dataObj = JSON.parse(res.data);
        console.log('解析后的data对象：', dataObj);
      } catch (error) {
        console.error('解析data失败：', error);
        ElMessage.error('模型数据格式错误（JSON解析失败）');
        return;
      }

      if (!dataObj || !Array.isArray(dataObj.weight_items)) {
        ElMessage.error('模型列表格式错误（weight_items不是数组）');
        return;
      }

      const filteredItems = dataObj.weight_items.filter((item: any) => {
        return item.value && item.value.includes(kind.value);
      });

      console.log('过滤后的模型列表：', filteredItems);
      state.weight_items = filteredItems;

      if (state.weight_items.length === 0) {
        ElMessage.info('未过滤到匹配模型，显示全部模型');
        state.weight_items = dataObj.weight_items;
      }

    })
    .catch((error) => {
      console.error('请求失败：', error);
      ElMessage.error('网络错误，无法加载模型列表');
    });
};

// 格式化识别结果标签
const formatLabel = (label: any) => {
  if (!label) return '无结果';
  if (Array.isArray(label)) {
    return label.join('、');
  }
  return label;
};

// 获取AI建议
const getAiSuggestion = () => {
  if (!state.predictionResult.label || (Array.isArray(state.predictionResult.label) && state.predictionResult.label.length === 0)) {
    state.aiSuggestion.content = '暂无识别结果，无法生成建议';
    return;
  }

  state.aiSuggestion.loading = true;
  
  let animalName = '';
  if (Array.isArray(state.predictionResult.label)) {
    animalName = state.predictionResult.label[0] || '';
  } else {
    animalName = state.predictionResult.label;
  }

  request.post('/api/suggest', {
    result: animalName,
    kind: state.form.kind
  }).then((res) => {
    state.aiSuggestion.loading = false;
    if (res.code === 0) {
      state.aiSuggestion.content = res.data?.suggestion || '暂无相关建议';
    } else {
      state.aiSuggestion.content = res.msg || '获取建议失败，请重试';
      ElMessage.error(res.msg || '获取建议失败');
    }
  }).catch((error) => {
    state.aiSuggestion.loading = false;
    console.error('建议接口请求失败:', error);
    state.aiSuggestion.content = '获取建议失败，请检查网络连接';
    ElMessage.error('网络错误，无法连接到建议服务');
  });
};

// 执行预测
const upData = () => {
  if (!state.img) return ElMessage.warning('请先上传图片');
  if (!weight.value) return ElMessage.warning('请选择模型');
  if (conf.value < 0 || conf.value > 100) return ElMessage.warning('置信度阈值需在0-100之间');

  state.form.weight = weight.value;
  state.form.conf = conf.value / 100;
  state.form.username = userInfos.value?.userName || '';
  state.form.inputImg = state.img;
  state.form.kind = kind.value;
  state.form.startTime = formatDate(new Date(), 'YYYY-mm-dd HH:MM:SS');

  request.post('/api/flask/predict', state.form).then((res) => {
    if (res.code === '0') {
      try {
        const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
        if (typeof data.label === 'string') {
          data.label = JSON.parse(data.label);
        }
        // 更新识别结果
        if (Array.isArray(data.label)) {
          state.predictionResult.label = data.label.map((item: string) => 
            item.replace(/\\u([\dA-Fa-f]{4})/g, (_, code: string) => 
              String.fromCharCode(parseInt(code, 16))
            )
          );
        }
        state.predictionResult.confidence = data.confidence;
        state.predictionResult.allTime = data.allTime;
        // 更新预测后图片
        if (data.outImg) predictedImageUrl.value = data.outImg;
        // 获取AI建议
        getAiSuggestion();
        ElMessage.success('预测成功！');
      } catch (error) {
        console.error('解析结果失败:', error);
        ElMessage.error('处理结果失败');
      }
    } else {
      ElMessage.error(res.msg);
    }
  }).catch((error) => {
    console.error('预测请求失败:', error);
    ElMessage.error('网络错误，预测失败');
  });
};

// 页面初始化逻辑
onMounted(() => {
  let unwatch: (() => void) | null = null;
  
  unwatch = watch(
    () => userInfos.value,
    (newVal) => {
      if (newVal && Object.keys(newVal).length > 0) {
        isUserInfoLoaded.value = true;
        if (kind.value) {
          getData();
        }
        if (unwatch) setTimeout(() => unwatch!(), 0);
      }
    },
    { immediate: true, deep: true }
  );

  if (state.kind_items.length > 0 && !kind.value) {
    kind.value = state.kind_items[0].value;
    setTimeout(() => {
      if (kind.value) {
        console.log('默认类别选中，触发模型加载');
        getData();
      }
    }, 300);
  }
});
</script>


<style scoped lang="scss">
/* 容器基础样式 */
.system-predict-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;

  .system-predict-padding {
    padding: 15px;
  }
}

/* 顶部控制栏样式 */
.header {
  width: 100%;
  height: 60px;
  display: flex;
  justify-content: start;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.predict-button {
  width: 100%;
}

/* 上部分三列布局 - 关键：确保容器高度严格一致 */
.upper-section {
  display: flex;
  gap: 20px;
  width: 100%;
  margin-bottom: 20px;
  height: calc(90vh - 140px); /* 固定总高度 */
}

.upper-column {
  flex: 1; /* 三列宽度均等 */
  height: 100%; /* 强制列高度与父容器一致 */
  display: flex;
  flex-direction: column; /* 子元素垂直排列 */
}

/* 卡片通用样式 - 确保卡片占满列高度 */
.card-header {
  font-size: 16px;
  font-weight: bold;
  padding: 12px 15px;
  border-bottom: 1px solid #eee;
  color: #333;
  background-color: #fafafa;
  height: 48px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between; /* 让标题和按钮左右分布 */
}

/* 更换图片按钮样式 */
.change-image-btn {
  color: #409eff;
  padding: 0;
  height: auto;
  font-size: 14px;
}

.change-image-btn:hover {
  color: #66b1ff;
  text-decoration: underline;
}

/* 图片卡片样式 - 强制卡片占满列高度 */
.image-card {
  width: 100%;
  height: 100%; /* 卡片高度与列一致 */
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 灰色内容区域 - 核心：三列内容区高度严格一致 */
.image-container {
  flex: 1; /* 占满卡片剩余高度（总高 - 头部高度） */
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background-color: #f9f9f9;
  box-sizing: border-box;
  min-height: 0;
}

/* 上传组件样式（核心修复） */
.avatar-uploader {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer; /* 始终显示可点击指针 */
}

.avatar {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
}

.avatar-uploader-icon {
  width: 100%;
  height: 80%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f5f5;
  color: #8c939d;
  font-size: 14px;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  cursor: pointer;
}

.upload-inner {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.empty-image {
  color: #999;
  font-size: 14px;
  text-align: center;
}

/* AI建议卡片样式 - 强制卡片占满列高度 */
.suggestion-card {
  width: 100%;
  height: 100%; /* 卡片高度与列一致 */
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 建议内容区域补充样式 */
.suggestion-content {
  flex: 1; /* 占满卡片剩余高度 */
  padding: 15px;
  overflow-y: auto; /* 内容超长时显示垂直滚动条 */
  overflow-x: hidden; /* 禁止水平滚动 */
  line-height: 1.7;
  background-color: #f9f9f9;
  box-sizing: border-box;
  
  /* 优化滚动条样式 */
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
  }
  &::-webkit-scrollbar-thumb {
    background: #ccc;
    border-radius: 3px;
  }
  &::-webkit-scrollbar-thumb:hover {
    background: #aaa;
  }
}

.empty-suggestion, .loading {
  color: #999;
  text-align: center;
  padding: 20px;
  font-size: 14px;
  width: 100%;
}

/* 下部分结果行布局 */
.lower-section {
  width: 100%;
  height: calc(10vh - 20px);
  min-height: 60px;
}

.result-card {
  width: 100%;
  height: 100%;
  border-radius: 10px;
  overflow: hidden;
}

.result-content {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 5px 15px;
  flex-wrap: wrap;
  gap: 15px;
}

.result-item {
  font-size: 13px;
}

.result-icon {
  color: #67c23a;
  width: 18px;
  height: 18px;
}

.result-label {
  font-size: 15px;
  font-weight: bold;
}

.result-value {
  font-size: 15px;
}

/* 响应式适配 */
@media (max-width: 1200px) {
  .upper-section {
    height: auto;
    min-height: 500px;
  }
  
  .upper-column {
    height: auto;
    min-height: 400px;
  }
  
  .lower-section {
    height: auto;
    min-height: 60px;
  }
}

@media (max-width: 768px) {
  .header {
    height: auto;
    flex-direction: column;
    align-items: flex-start;
  }
  
  .result-item {
    width: 100%;
    justify-content: center;
    font-size: 12px;
  }
}
</style>
