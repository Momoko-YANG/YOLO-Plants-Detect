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

      <!-- 主要内容区域：左右布局 -->
      <div class="main-content">
        <!-- 左侧：图片预览区域 -->
        <div class="left-section">
          <el-card shadow="hover" class="image-card">
            <el-upload 
              v-model="state.img" 
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
          </el-card>
        </div>

        <!-- 右侧：结果和建议区域 -->
        <div class="right-section">
          <!-- 上部：识别结果 -->
          <el-card class="result-card" v-if="state.predictionResult.label || state.showResultCard">
            <div class="result-header">识别结果</div>
            <div class="result-content">
              <div class="result-item">
                <!-- 类别图标 -->
                <el-icon class="result-icon"><Category /></el-icon>
                <span class="result-label">类别：</span>
                <span class="result-value">{{ formatLabel(state.predictionResult.label) }}</span>
              </div>
              <div class="result-item">
                <!-- 概率图标 -->
                <el-icon class="result-icon"><Percent /></el-icon>
                <span class="result-label">预测概率：</span>
                <span class="result-value">{{ state.predictionResult.confidence }}</span>
              </div>
              <div class="result-item">
                <!-- 时间图标 -->
                <el-icon class="result-icon"><Clock /></el-icon>
                <span class="result-label">总时间：</span>
                <span class="result-value">{{ state.predictionResult.allTime }}</span>
              </div>
            </div>
          </el-card>

          <!-- 下部：AI建议 -->
          <el-card class="suggestion-card" v-if="state.aiSuggestion || state.showSuggestionCard">
            <div class="suggestion-header">AI建议</div>
            <div class="suggestion-content">
              <template v-if="state.aiSuggestion.loading">
                <div class="loading">加载中...</div>
              </template>
              <template v-else-if="state.aiSuggestion.content">
                <div v-html="state.aiSuggestion.content"></div>
              </template>
              <template v-else>
                <div class="empty-suggestion">完成识别后将显示AI建议</div>
              </template>
            </div>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="personal">
import { reactive, ref, onMounted, watch } from 'vue';
import type { UploadInstance, UploadProps } from 'element-plus';
// 导入需要的图标
import { Category, Percent, Clock } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import request from '/@/utils/request';
import { useUserInfo } from '/@/stores/userInfo';
import { storeToRefs } from 'pinia';
import { formatDate } from '/@/utils/formatTime';

// 响应式变量
const imageUrl = ref('');
const conf = ref(50);
const weight = ref('');
const kind = ref(''); // 初始化为空，后续会被默认值填充
const uploadFile = ref<UploadInstance>();
const stores = useUserInfo();
const { userInfos } = storeToRefs(stores);
const isUserInfoLoaded = ref(false);

const state = reactive({
  weight_items: [] as { value: string; label: string }[], // 明确模型列表类型
  kind_items: [
    { value: 'fire', label: '火灾烟雾检测' }
  ],
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
  showResultCard: false,
  showSuggestionCard: false,
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

// 处理图片上传成功
const handleAvatarSuccessone: UploadProps['onSuccess'] = (response, uploadFile) => {
  imageUrl.value = URL.createObjectURL(uploadFile.raw!);
  state.img = response.data;
  state.showResultCard = true;
  state.showSuggestionCard = true;
};

// 获取模型列表
const getData = () => {
  console.log('触发模型列表加载，当前类别：', kind.value);

  // 重置模型列表
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
        if (Array.isArray(data.label)) {
          state.predictionResult.label = data.label.map((item: string) => 
            item.replace(/\\u([\dA-Fa-f]{4})/g, (_, code: string) => 
              String.fromCharCode(parseInt(code, 16))
            )
          );
        }
        state.predictionResult.confidence = data.confidence;
        state.predictionResult.allTime = data.allTime;
        if (data.outImg) imageUrl.value = data.outImg;
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
/* 样式保持不变，增加图标相关样式 */
.system-predict-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;

  .system-predict-padding {
    padding: 15px;
  }
}

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

.main-content {
  display: flex;
  gap: 20px;
  width: 100%;
  height: calc(100vh - 100px);
}

.left-section {
  flex: 1;
  height: 100%;
}

.image-card {
  width: 100%;
  height: 100%;
  border-radius: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.avatar-uploader .avatar {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.avatar-uploader-icon {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f5f5;
  color: #8c939d;
  font-size: 16px;
  border: 1px dashed #d9d9d9;
}

.right-section {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-card, .suggestion-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  overflow: hidden;
}

.result-header, .suggestion-header {
  font-size: 18px;
  font-weight: bold;
  padding: 15px;
  border-bottom: 1px solid #eee;
  color: #333;
}

.result-content, .suggestion-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  line-height: 1.6;
}

.result-item {
  display: flex;
  margin-bottom: 10px;
  align-items: center; /* 新增：让图标和文字垂直居中 */
}

/* 新增：图标样式 */
.result-icon {
  margin-right: 8px;
  color: #67c23a; /* 绿色图标，可根据需要调整 */
  width: 18px;
  height: 18px;
}

.result-label {
  font-weight: 500;
  color: #666;
  min-width: 80px;
}

.result-value {
  color: #333;
  word-break: break-all;
}

.empty-suggestion {
  color: #999;
  text-align: center;
  padding: 20px;
}

.loading {
  color: #666;
  text-align: center;
  padding: 20px;
}

.button-section {
  display: flex;
  justify-content: center;
}

.predict-button {
  width: 100%;
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  
  .left-section, .right-section {
    height: auto;
    min-height: 400px;
  }
}
</style>
