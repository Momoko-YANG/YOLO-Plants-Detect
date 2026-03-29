<template>
	<div class="statistics-container layout-padding">
		<div class="layout-padding-auto layout-padding-view">
			<!-- 标题 -->
			<!-- <h2 class="mb15">识别数据统计分析</h2> -->
			
			<!-- 田字格布局：2行2列（外层加左右内边距） -->
			<div class="chart-grid">
				<!-- 1. 识别标签分布（柱状图+折线图结合） -->
				<div class="chart-item">
					<h3>识别标签分布</h3>
					<div ref="kindCountChartRef" class="chart"></div>
				</div>

				<!-- 2. 用户平均识别置信度（饼图） -->
				<div class="chart-item">
					<h3>用户平均识别置信度(%)</h3>
					<div ref="userAvgConfChartRef" class="chart"></div>
				</div>

				<!-- 3. 用户识别次数统计（柱状图） -->
				<div class="chart-item">
					<h3>用户识别次数统计</h3>
					<div ref="userPredictCountChartRef" class="chart"></div>
				</div>

				<!-- 4. 识别耗时时长趋势（折线图） -->
				<div class="chart-item">
					<h3>识别耗时时长趋势(秒)</h3>
					<div ref="timeConsumeChartRef" class="chart"></div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts" name="statisticsAnalysis">
import { reactive, onMounted, ref, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import request from '/@/utils/request';
import { ElMessage } from 'element-plus';

// 定义图表Ref引用
const kindCountChartRef = ref<HTMLElement | null>(null);
const userAvgConfChartRef = ref<HTMLElement | null>(null);
const userPredictCountChartRef = ref<HTMLElement | null>(null);
const timeConsumeChartRef = ref<HTMLElement | null>(null);

// 定义图表实例
const chartInstances = reactive({
	kindCount: null as echarts.ECharts | null,
	userAvgConf: null as echarts.ECharts | null,
	userPredictCount: null as echarts.ECharts | null,
	timeConsume: null as echarts.ECharts | null,
});

// 定义状态数据
const state = reactive({
	statisticsData: {
		labelCount: {} as Record<string, number>,
		userAvgConf: {} as Record<string, number>,
		userPredictCount: {} as Record<string, number>,
		timeConsumeList: [] as Array<{
			id: number;
			username: string;
			kind: string;
			consumeTime: number;
			startTime: string;
			label: string;
		}>
	},
	loading: false
});

// 初始化图表
const initCharts = () => {
	// 1. 识别标签分布（核心修改：柱状图+折线图结合）
	if (kindCountChartRef.value) {
		chartInstances.kindCount = echarts.init(kindCountChartRef.value);
		// 提取标签和对应数量
		const labels = Object.keys(state.statisticsData.labelCount);
		const counts = Object.values(state.statisticsData.labelCount);
		
		chartInstances.kindCount.setOption({
			title: { text: '', left: 'center' },
			tooltip: { 
				trigger: 'axis',
				axisPointer: { type: 'cross' } // 十字准星提示
			},
			// 双Y轴配置（柱状图用左Y轴，折线图用右Y轴）
			yAxis: [
				{
					type: 'value',
					name: '标签数量',
					axisLine: { lineStyle: { color: '#5470c6' } },
					axisLabel: { formatter: '{value} 次' }
				},
				{
					type: 'value',
					name: '数量趋势',
					axisLine: { lineStyle: { color: '#ee6666' } },
					axisLabel: { formatter: '{value} 次' },
					// 和左Y轴值域一致，保证刻度对齐
					min: Math.min(...counts) - 1,
					max: Math.max(...counts) + 1
				}
			],
			xAxis: {
				type: 'category',
				data: labels,
				axisLabel: { interval: 0 }
			},
			series: [
				// 柱状图：展示标签数量
				{
					name: '标签数量',
					type: 'bar',
					yAxisIndex: 0, // 关联左Y轴
					data: counts,
					itemStyle: { color: '#5470c6' },
					label: {
						show: true,
						position: 'top',
						formatter: '{c}次'
					}
				},
				// 折线图：展示数量趋势
				{
					name: '数量趋势',
					type: 'line',
					yAxisIndex: 1, // 关联右Y轴
					data: counts,
					itemStyle: { color: '#ee6666' },
					lineStyle: { width: 3 },
					markPoint: { // 标记最大值/最小值
						data: [
							{ type: 'max', name: '最大值' },
							{ type: 'min', name: '最小值' }
						]
					},
					markLine: { // 展示平均值线
						data: [{ type: 'average', name: '平均值' }]
					},
					label: {
						show: true,
						position: 'bottom',
						formatter: '{c}次'
					}
				}
			],
			// 图例配置
			legend: {
				data: ['标签数量', '数量趋势'],
				top: 0
			}
		});
	}

	// 2. 用户平均置信度 饼图（无修改）
	if (userAvgConfChartRef.value) {
		chartInstances.userAvgConf = echarts.init(userAvgConfChartRef.value);
		chartInstances.userAvgConf.setOption({
			title: { text: '', left: 'center' },
			tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
			series: [
				{
					name: '平均置信度',
					type: 'pie',
					radius: ['40%', '70%'],
					data: Object.entries(state.statisticsData.userAvgConf).map(([user, conf]) => ({ 
						name: user, 
						value: parseFloat(conf.toFixed(2)) 
					})),
					label: {
						show: true,
						formatter: '{b}: {c}%'
					}
				}
			]
		});
	}

	// 3. 用户识别次数柱状图（无修改）
	if (userPredictCountChartRef.value) {
		chartInstances.userPredictCount = echarts.init(userPredictCountChartRef.value);
		chartInstances.userPredictCount.setOption({
			title: { text: '', left: 'center' },
			tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
			xAxis: {
				type: 'category',
				data: Object.keys(state.statisticsData.userPredictCount),
				axisLabel: { interval: 0 }
			},
			yAxis: { type: 'value', name: '次数' },
			series: [
				{
					name: '识别次数',
					type: 'bar',
					data: Object.values(state.statisticsData.userPredictCount),
					label: {
						show: true,
						position: 'top',
						formatter: '{c}次'
					}
				}
			]
		});
	}

	// 4. 识别耗时折线图（无修改）
	if (timeConsumeChartRef.value) {
		chartInstances.timeConsume = echarts.init(timeConsumeChartRef.value);
		const sortedTimeData = [...state.statisticsData.timeConsumeList].sort((a, b) => a.id - b.id);
		const xData = sortedTimeData.map(item => `记录${item.id}`);
		const yData = sortedTimeData.map(item => parseFloat(item.consumeTime.toFixed(3)));
		
		chartInstances.timeConsume.setOption({
			title: { text: '', left: 'center' },
			tooltip: { trigger: 'axis' },
			xAxis: {
				type: 'category',
				data: xData,
				axisLabel: { 
					interval: 0,
					rotate: 30 
				}
			},
			yAxis: { type: 'value', name: '耗时(秒)' },
			series: [
				{
					name: '识别耗时',
					type: 'line',
					data: yData,
					smooth: true,
					markPoint: {
						data: [
							{ type: 'max', name: '最大值' },
							{ type: 'min', name: '最小值' }
						]
					},
					label: {
						show: true,
						position: 'top',
						formatter: '{c}s'
					}
				}
			]
		});
	}
};

// 自适应调整图表大小
const resizeCharts = () => {
	Object.values(chartInstances).forEach(instance => {
		if (instance) {
			instance.resize();
		}
	});
};

// 加载统计数据
const loadStatisticsData = async () => {
	state.loading = true;
	try {
		const res = await request.get('/api/imgRecords/statistics');
		if (res.code === "0") { 
			state.statisticsData = res.data;
			initCharts();
			ElMessage({
				type: 'success',
				message: '统计数据加载成功'
			});
		} else {
			ElMessage({
				type: 'error',
				message: `获取统计数据失败：${res.msg}`
			});
		}
	} catch (error) {
		console.error('统计接口调用失败：', error);
		ElMessage({
			type: 'error',
			message: '获取统计数据失败，请检查接口是否正常'
		});
	} finally {
		state.loading = false;
	}
};

// 页面挂载/卸载逻辑
onMounted(() => {
	loadStatisticsData();
	window.addEventListener('resize', resizeCharts);
});

onUnmounted(() => {
	window.removeEventListener('resize', resizeCharts);
	Object.values(chartInstances).forEach(instance => {
		if (instance) {
			instance.dispose();
		}
	});
});
</script>

<style scoped lang="scss">
.statistics-container {
	width: 100%;
	height: calc(100vh - 120px); // 适配页面高度
	overflow: hidden;
	padding: 0 20px; // 外层整体左右空隙
	box-sizing: border-box; // 保证padding不超出容器

	// 田字格核心布局：2行2列
	.chart-grid {
		display: grid;
		grid-template-columns: 1fr 1fr; // 2列均分
		grid-template-rows: 1fr 1fr; // 2行均分
		gap: 15px; // 图表之间的间距
		width: 100%;
		height: 100%;
	}

	.chart-item {
		background: #fff;
		padding: 15px 20px; // 每个图表项的左右内边距
		border-radius: 8px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
		box-sizing: border-box; // 防止padding撑大容器

		h3 {
			margin: 0 0 10px 0;
			font-size: 16px;
			color: #333;
			font-weight: 600;
			flex-shrink: 0; // 标题不压缩
		}

		// 图表容器占满剩余高度
		.chart {
			flex: 1;
			width: 100%;
			height: 0; // 配合flex:1自动拉伸高度
			min-height: 200px; // 最小高度保障
		}
	}
}

// 响应式适配：小屏幕改为1列
@media (max-width: 768px) {
	.statistics-container {
		padding: 0 10px; // 移动端空隙适当减小
	}
	.statistics-container .chart-grid {
		grid-template-columns: 1fr;
		grid-template-rows: repeat(4, 1fr);
	}
	.chart-item {
		padding: 15px 10px; // 移动端图表内空隙减小
	}
}
</style>