package com.example.Kcsj.controller;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.Kcsj.common.Result;
import com.example.Kcsj.entity.ImgRecords;
import com.example.Kcsj.mapper.ImgRecordsMapper;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/imgRecords")
public class ImgRecordsController {
    @Resource
    ImgRecordsMapper imgRecordsMapper;

    @GetMapping("/all")
    public Result<?> GetAll() {
        return Result.success(imgRecordsMapper.selectList(null));
    }
    @GetMapping("/{id}")
    public Result<?> getById(@PathVariable int id) {
        System.out.println(id);
        return Result.success(imgRecordsMapper.selectById(id));
    }

    @GetMapping
    public Result<?> findPage(@RequestParam(defaultValue = "1") Integer pageNum,
                              @RequestParam(defaultValue = "10") Integer pageSize,
                              @RequestParam(defaultValue = "") String search,
                              @RequestParam(defaultValue = "") String search1,
                              @RequestParam(defaultValue = "") String search3,
                              @RequestParam(defaultValue = "") String search2) {
        LambdaQueryWrapper<ImgRecords> wrapper = Wrappers.<ImgRecords>lambdaQuery();
        wrapper.orderByDesc(ImgRecords::getStartTime);
        if (StrUtil.isNotBlank(search)) {
            wrapper.like(ImgRecords::getUsername, search);
        }
        if (StrUtil.isNotBlank(search1)) {
            wrapper.like(ImgRecords::getKind, search1);
        }
        if (StrUtil.isNotBlank(search2)) {
            wrapper.like(ImgRecords::getLable, search2);
        }
        if (StrUtil.isNotBlank(search3)) {
            wrapper.like(ImgRecords::getConf, search3);
        }
        Page<ImgRecords> Page = imgRecordsMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
        return Result.success(Page);
    }

    @DeleteMapping("/{id}")
    public Result<?> delete(@PathVariable int id) {
        imgRecordsMapper.deleteById(id);
        return Result.success();
    }

    @PostMapping("/update")
    public Result<?> updates(@RequestBody ImgRecords imgrecords) {
        imgRecordsMapper.updateById(imgrecords);
        return Result.success();
    }


    @PostMapping
    public Result<?> save(@RequestBody ImgRecords imgrecords) {
        System.out.println(imgrecords);
        imgRecordsMapper.insert(imgrecords);
        return Result.success();
    }


    // 完善后的统计接口（基于confidence字段计算置信度）
// 完善后的统计接口（基于label字段统计识别类别）
    @GetMapping("/statistics")
    public Result<?> findAllData() {
        // 1. 查询全表数据
        List<ImgRecords> allRecords = imgRecordsMapper.selectList(null);

        // 2. 统计1：从label数组中统计不同识别类别（如"火"/"烟"/"HUO"）的个数
        Map<String, Long> labelCount = new HashMap<>();
        allRecords.stream()
                .filter(record -> StrUtil.isNotBlank(record.getLabel())) // 过滤空label
                .forEach(record -> {
                    // 解析label字符串数组 ["火", "烟", "HUO"]
                    List<String> labelList = JSONUtil.toList(record.getLabel(), String.class);
                    // 遍历每个标签，统计次数
                    labelList.forEach(label -> {
                        if (StrUtil.isNotBlank(label)) { // 过滤空标签
                            labelCount.put(label, labelCount.getOrDefault(label, 0L) + 1);
                        }
                    });
                });

        // 3. 统计2：不同用户的平均识别置信度（基于confidence字段）
        Map<String, Double> userAvgConf = allRecords.stream()
                .filter(record -> StrUtil.isNotBlank(record.getUsername()) && StrUtil.isNotBlank(record.getConfidence()))
                .collect(Collectors.groupingBy(
                        ImgRecords::getUsername,
                        Collectors.averagingDouble(record -> {
                            // 解析confidence字符串数组 ["67.29%", "22.13%"]
                            List<String> confList = JSONUtil.toList(record.getConfidence(), String.class);
                            if (confList.isEmpty()) {
                                return 0.0;
                            }
                            // 去除%号并转为Double，计算单条记录的置信度平均值
                            double sum = 0.0;
                            for (String conf : confList) {
                                try {
                                    sum += Double.parseDouble(conf.replace("%", "").trim());
                                } catch (NumberFormatException e) {
                                    sum += 0.0;
                                }
                            }
                            return sum / confList.size();
                        })
                ));

        // 4. 统计3：不同用户的预测次数
        Map<String, Long> userPredictCount = allRecords.stream()
                .filter(record -> StrUtil.isNotBlank(record.getUsername()))
                .collect(Collectors.groupingBy(ImgRecords::getUsername, Collectors.counting()));

        // 5. 统计4：每次识别的耗时时长（清洗all_time字段）
        List<Map<String, Object>> timeConsumeList = allRecords.stream()
                .filter(record -> StrUtil.isNotBlank(record.getAllTime()) && record.getAllTime().contains("秒"))
                .map(record -> {
                    Map<String, Object> timeMap = new HashMap<>();
                    timeMap.put("id", record.getId());
                    timeMap.put("username", record.getUsername());
                    // 补充label信息，便于前端关联展示
                    timeMap.put("label", record.getLabel());
                    timeMap.put("kind", record.getKind());
                    // 提取数值部分
                    String timeStr = record.getAllTime().replace("秒", "").trim();
                    try {
                        timeMap.put("consumeTime", Double.parseDouble(timeStr));
                    } catch (NumberFormatException e) {
                        timeMap.put("consumeTime", 0.0);
                    }
                    timeMap.put("startTime", record.getStartTime());
                    return timeMap;
                })
                .collect(Collectors.toList());

        // 6. 封装返回结果（key改为labelCount，更贴合实际统计维度）
        Map<String, Object> resultMap = new HashMap<>();
        resultMap.put("labelCount", labelCount); // 替换原kindCount，统计label中的具体类别
        resultMap.put("userAvgConf", userAvgConf);
        resultMap.put("userPredictCount", userPredictCount);
        resultMap.put("timeConsumeList", timeConsumeList);

        return Result.success(resultMap);
    }
}
