<template>
	<div class="system-predict-container layout-padding">
		<div class="system-predict-padding layout layout-padding-auto layout-padding-view">
			<div class="header">
				<div class="kind">
					<el-select v-model="kind" placeholder="请选择识别类别" size="large" style="width: 180px" @change="getData">
						<el-option v-for="item in state.kind_items" :key="item.value" :label="item.label"
							:value="item.value" />
					</el-select>
				</div>
				<div class="weight">
					<el-select v-model="weight" placeholder="请选择模型" size="large" style="margin-left: 20px;width: 180px">
						<el-option v-for="item in state.weight_items" :key="item.value" :label="item.label"
							:value="item.value" />
					</el-select>
				</div>
				<div class="conf" style="margin-left: 20px;display: flex; flex-direction: row;">
					<div
						style="font-size: 14px;margin-right: 20px;display: flex;justify-content: start;align-items: center;color: #909399;">
						设置最小置信度阈值</div>
					<el-slider v-model="conf" :format-tooltip="formatTooltip" style="width: 280px;" />
				</div>
				<el-upload v-model="state.form.inputVideo" ref="uploadFile" class="avatar-uploader"
					action="http://localhost:9999/files/upload" :show-file-list="false"
					:on-success="handleAvatarSuccessone">
					<div class="button-section" style="margin-left: 20px">
						<el-button type="info" class="predict-button">上传视频</el-button>
					</div>
				</el-upload>
				<div class="button-section" style="margin-left: 20px">
					<el-button type="primary" @click="upData" class="predict-button">开始处理</el-button>
				</div>
				<div class="demo-progress" v-if="state.isShow">
					<el-progress :text-inside="true" :stroke-width="20" :percentage=state.percentage style="width: 380px;">
						<span>{{ state.type_text }} {{ state.percentage }}%</span>
					</el-progress>
				</div>
			</div>
			<!-- 左右布局容器 -->
			<div class="content-container">
				<!-- 左侧80%视频区域 -->
				<div class="cards" ref="cardsContainer">
					<img v-if="state.video_path" class="video" :src="state.video_path">
				</div>
				<!-- 右侧20%AI建议区域 -->
				<div class="ai-suggestion">
					<h3>AI识别建议</h3>
					<div class="suggestion-content">
						<!-- 基础统计信息 -->
						<div v-if="state.mostFrequentClass" class="stat-item">
							<span class="label">出现次数最多的类别：</span>
							<span class="value">{{ state.mostFrequentClass.name || '未知类别' }}</span>
						</div>
						<div v-if="state.mostFrequentClass && state.mostFrequentClass.count !== undefined" class="stat-item">
							<span class="label">出现总次数：</span>
							<span class="value">{{ state.mostFrequentClass.count }}</span>
						</div>
						<div v-if="state.totalFrames > 0" class="stat-item">
							<span class="label">视频总帧数：</span>
							<span class="value">{{ state.totalFrames }}</span>
						</div>
						
						<!-- 类别描述信息（新增） -->
						<div v-if="state.mostFrequentClass?.desc" class="description-item">
							<span class="label">类别描述：</span>
							<div class="description-content" v-html="state.mostFrequentClass.desc"></div>
						</div>
						
						<div v-else class="empty-state">
							<p>请上传视频并点击开始处理</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>


<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import request from '/@/utils/request';
import { useUserInfo } from '/@/stores/userInfo';
import { storeToRefs } from 'pinia';
import type { UploadInstance, UploadProps } from 'element-plus';
import { SocketService } from '/@/utils/socket';
import { formatDate } from '/@/utils/formatTime';
import kindConfig from '/@/config/kindConfig.json';

const uploadFile = ref<UploadInstance>();
const stores = useUserInfo();
const conf = ref('50'); // 默认值避免空值
const kind = ref('');
const weight = ref('');
const { userInfos } = storeToRefs(stores);

const handleAvatarSuccessone: UploadProps['onSuccess'] = (response, uploadFile) => {
	ElMessage.success('上传成功！');
	state.form.inputVideo = response.data;
};

const state = reactive({
	weight_items: [] as any,
	kind_items: kindConfig.kind_items,
	data: {} as any,
	video_path: '',
	// 新增desc字段接收描述信息
	mostFrequentClass: null as { name: string, count: number, desc?: string } | null,
	totalFrames: 0,
	type_text: "正在保存",
	percentage: 0,
	isShow: false,
	form: {
		username: '',
		inputVideo: null as any,
		weight: '',
		conf: null as any,
		kind: '',
		startTime: ''
	},
});

const socketService = new SocketService();

// 核心修改：接收并处理包含desc的消息
socketService.on('most_frequent_class', (data) => {
	console.log("接收的类别数据:", data);
	// 严格校验数据格式
	if (typeof data === 'object' && data !== null) {
		// 确保包含必要字段，缺失时用默认值
		state.mostFrequentClass = {
			name: data.name || '未识别到类别',
			count: typeof data.count === 'number' ? data.count : 0,
			desc: data.desc || '' // 新增：接收描述信息
		};
		ElMessage.success(`最频繁类别：${state.mostFrequentClass.name}（出现${state.mostFrequentClass.count}次）`);
	} else if (typeof data === 'string') {
		// 兼容后端直接返回字符串的情况
		state.mostFrequentClass = {
			name: data,
			count: 0,
			desc: ''
		};
	} else {
		// 数据格式错误时的安全处理
		state.mostFrequentClass = {
			name: '识别数据异常',
			count: 0,
			desc: ''
		};
		ElMessage.error('无法解析识别结果，请重试');
	}
});

socketService.on('total_frames', (count) => {
	// 确保帧数是数字
	state.totalFrames = typeof count === 'number' ? count : 0;
});

socketService.on('message', (data) => {
	console.log('Received message:', data);
	ElMessage.success(data);
});

const formatTooltip = (val: number) => {
	return val / 100
};

socketService.on('progress', (data) => {
	const progress = parseInt(data);
	state.percentage = isNaN(progress) ? 0 : progress;
	state.isShow = state.percentage < 100;
	
	if (state.percentage === 100) {
		ElMessage.success("保存成功！");
		setTimeout(() => {
			state.isShow = false;
			state.percentage = 0;
		}, 2000);
	}
});

const getData = () => {
	request.get('/api/flask/file_names').then((res) => {
		if (res.code == 0) {
			res.data = JSON.parse(res.data);
			state.weight_items = res.data.weight_items.filter(item => item.value.includes(kind.value));
		} else {
			ElMessage.error(res.msg);
		}
	}).catch(err => {
		ElMessage.error('获取模型列表失败');
		console.error(err);
	});
};

const upData = () => {
	// 输入验证
	if (!state.form.inputVideo) {
		ElMessage.error('请先上传视频');
		return;
	}
	if (!weight.value) {
		ElMessage.error('请选择模型');
		return;
	}
	if (isNaN(parseFloat(conf.value)) || parseFloat(conf.value) < 0 || parseFloat(conf.value) > 100) {
		ElMessage.error('请设置有效的置信度阈值（0-100）');
		return;
	}
	
	// 重置状态
	state.mostFrequentClass = null;
	state.totalFrames = 0;
	state.isShow = true;
	state.percentage = 0;
	
	state.form.weight = weight.value;
	state.form.conf = parseFloat(conf.value) / 100;
	state.form.username = userInfos.value.userName || 'unknown';
	state.form.kind = kind.value;
	state.form.startTime = formatDate(new Date(), 'YYYY-mm-dd HH:MM:SS');
	
	const queryParams = new URLSearchParams({
		...(state.form as any),
		clientId: socketService.getId() || '',
	}).toString();
	state.video_path = `http://127.0.0.1:9999/predictVideo?${queryParams}`;
	ElMessage.success('开始处理视频...');
};

onMounted(() => {
	getData();
});
</script>

<style scoped lang="scss">
.system-predict-container {
	width: 100%;
	height: 100%;
	display: flex;
	flex-direction: column;
}

.system-predict-padding {
	padding: 15px;
	background: radial-gradient(circle, #d3e3f1 0%, #ffffff 100%);

	.el-table {
		flex: 1;
	}
}

.header {
	width: 100%;
	height: 60px; /* 固定高度避免布局抖动 */
	display: flex;
	justify-content: start;
	align-items: center;
	flex-wrap: wrap; /* 适配小屏幕 */
	gap: 10px;
}

.content-container {
	width: 100%;
	height: calc(100% - 75px);
	display: flex;
	gap: 15px;
	margin-top: 15px;
}

.cards {
	width: 80%;
	height: 100%;
	border-radius: 5px;
	padding: 0px;
	overflow: hidden;
	display: flex;
	justify-content: center;
	align-items: center;
	background: radial-gradient(circle, #d3e3f1 0%, #ffffff 100%);
}

.video {
	width: 100%;
	max-height: 100%;
	height: auto;
	object-fit: contain;
}

.ai-suggestion {
	width: 20%;
	height: 100%;
	border-radius: 5px;
	padding: 15px;
	background: radial-gradient(circle, #d3e3f1 0%, #ffffff 100%);
	display: flex;
	flex-direction: column;
	overflow-y: auto; /* 新增：描述过长时可滚动 */
}

.ai-suggestion h3 {
	margin: 0 0 20px 0;
	padding-bottom: 10px;
	border-bottom: 1px solid #e0e0e0;
	color: #333;
	font-size: 16px;
}

.suggestion-content {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 15px;
}

.stat-item {
	padding: 12px;
	background: #f8fafc;
	border-radius: 4px;
	border-left: 3px solid #3b82f6;
}

/* 新增：描述信息样式 */
.description-item {
	padding: 12px;
	background: #f8fafc;
	border-radius: 4px;
	border-left: 3px solid #10b981; /* 用不同颜色区分 */
}

.description-content {
	margin-top: 8px;
	color: #1e293b;
	font-size: 14px;
	line-height: 1.6; /* 优化行高，提升可读性 */
	white-space: pre-wrap; /* 保留换行符 */
}

.label {
	color: #64748b;
	font-size: 14px;
	font-weight: 500; /* 加粗标签文字 */
}

.value {
	color: #1e293b;
	font-weight: 600;
	margin-left: 8px;
}

.empty-state {
	flex: 1;
	display: flex;
	justify-content: center;
	align-items: center;
	color: #94a3b8;
	font-size: 14px;
}

.button-section {
	display: flex;
	justify-content: center;
}

.predict-button {
	width: 100%;
}

.demo-progress .el-progress--line {
	margin-left: 20px;
	width: 600px;
}

/* 响应式调整 */
@media (max-width: 1200px) {
	.demo-progress .el-progress--line {
		width: 300px;
	}
	.content-container {
		flex-direction: column; /* 小屏幕下上下布局 */
	}
	.cards, .ai-suggestion {
		width: 100%;
		height: auto;
	}
	.ai-suggestion {
		margin-top: 15px;
		max-height: 400px;
	}
}
</style>
