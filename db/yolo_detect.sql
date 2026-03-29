/*
 Navicat Premium Data Transfer

 Source Server         : mysql8.1-localhost
 Source Server Type    : MySQL
 Source Server Version : 80100 (8.1.0)
 Source Host           : localhost:3306
 Source Schema         : yolo_detect

 Target Server Type    : MySQL
 Target Server Version : 80100 (8.1.0)
 File Encoding         : 65001

 Date: 20/01/2026 01:26:11
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for camerarecords
-- ----------------------------
DROP TABLE IF EXISTS `camerarecords`;
CREATE TABLE `camerarecords`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `weight` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `conf` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `start_time` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `out_video` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `kind` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 45 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of camerarecords
-- ----------------------------
INSERT INTO `camerarecords` VALUES (44, 'plants_best.pt', '0.18', 'admin', '2026-01-20 01:12:14', 'http://localhost:9999/files/3c97f14168504580b391c564f5dd3e46_output.mp4', 'plants');

-- ----------------------------
-- Table structure for imgrecords
-- ----------------------------
DROP TABLE IF EXISTS `imgrecords`;
CREATE TABLE `imgrecords`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `input_img` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `out_img` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `confidence` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `all_time` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `conf` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `weight` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `start_time` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `label` varchar(5000) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `kind` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 249 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of imgrecords
-- ----------------------------
INSERT INTO `imgrecords` VALUES (243, 'http://localhost:9999/files/0a7c8de3d37e47eba4c35b50747a22e7_0000_jpg.rf.8eec055223fc07a671b88bb70251b93c.jpg', 'http://localhost:9999/files/080e849265a54b9c98f968323f6024c3_result.jpg', '[\"46.78%\", \"45.07%\"]', '4.160秒', '0.13', 'plants_best.pt', 'admin', '2026-01-20 01:07:54', '[\"\\u82f9\\u679c\\u9ed1\\u661f\\u75c5\\u53f6\", \"\\u82f9\\u679c\\u9ed1\\u661f\\u75c5\\u53f6\"]', 'plants');
INSERT INTO `imgrecords` VALUES (244, 'http://localhost:9999/files/4509a44dbf09418fbb07e018217e9cad_Early_Blight_of_Tomato1687_jpg.rf.9bb5cfb92e78ebcbdd6c32ee2132e1eb.jpg', 'http://localhost:9999/files/25256b9b9e4a48668fe36021b5f0e9b5_result.jpg', '[\"32.32%\"]', '3.917秒', '0.11', 'plants_best.pt', 'admin', '2026-01-20 01:09:31', '[\"\\u756a\\u8304\\u665a\\u75ab\\u75c5\\u53f6\"]', 'plants');
INSERT INTO `imgrecords` VALUES (245, 'http://localhost:9999/files/0a57c598f5544ef1aa34696b8640ef08_southern-rust-close_jpg.rf.55bf1e40e5c09cbb8ca3234a8597835d.jpg', 'http://localhost:9999/files/984968487d8f45e0bb3dd31c3db4e7d6_result.jpg', '[\"87.06%\", \"30.59%\"]', '3.620秒', '0.11', 'plants_best.pt', 'admin', '2026-01-20 01:10:20', '[\"\\u7389\\u7c73\\u9508\\u75c5\\u53f6\", \"\\u82f9\\u679c\\u9508\\u75c5\\u53f6\"]', 'plants');
INSERT INTO `imgrecords` VALUES (246, 'http://localhost:9999/files/ed95a152ddfc4cfb8a9f77f9aaa138c3_0796_52srusttelia_jpg.rf.6dbd03c2f90491f4945f89b2e19e1d0a.jpg', 'http://localhost:9999/files/dbceb833a20b4421bd7a57f0e9e5d4ac_result.jpg', '[\"88.48%\"]', '3.846秒', '0.14', 'plants_best.pt', 'admin', '2026-01-20 01:12:55', '[\"\\u7389\\u7c73\\u9508\\u75c5\\u53f6\"]', 'plants');
INSERT INTO `imgrecords` VALUES (247, 'http://localhost:9999/files/5b5a616d47824d8aad67c85ac39c8afc_9167d851305baf06649c57aea130c8fb_jpg.rf.46c6ad49728bfecb652a237edf1aa5fb.jpg', 'http://localhost:9999/files/c97254f495684f2fb71eb1880da8697f_result.jpg', '[\"97.46%\", \"95.17%\", \"95.07%\", \"94.34%\", \"94.19%\", \"92.97%\", \"92.53%\", \"92.33%\", \"86.62%\", \"1.10%\"]', '4.468秒', '0.01', 'plants_best.pt', 'admin', '2026-01-20 01:14:55', '[\"\\u84dd\\u8393\\u53f6\\u7247\", \"\\u84dd\\u8393\\u53f6\\u7247\", \"\\u84dd\\u8393\\u53f6\\u7247\", \"\\u84dd\\u8393\\u53f6\\u7247\", \"\\u84dd\\u8393\\u53f6\\u7247\", \"\\u84dd\\u8393\\u53f6\\u7247\", \"\\u84dd\\u8393\\u53f6\\u7247\", \"\\u84dd\\u8393\\u53f6\\u7247\", \"\\u84dd\\u8393\\u53f6\\u7247\", \"\\u84dd\\u8393\\u53f6\\u7247\"]', 'plants');
INSERT INTO `imgrecords` VALUES (248, 'http://localhost:9999/files/22ac96e87cc44bb58d2b6589c8186bde_7-17-Photo3_Septoria-MARY_jpg.rf.a09085adc57f7dc5165eae0d5ac95b9f.jpg', 'http://localhost:9999/files/7b7cc98bf35e4ac296a81243a8bbe515_result.jpg', '[\"72.36%\", \"65.67%\", \"45.24%\", \"31.54%\"]', '4.099秒', '0.09', 'plants_best.pt', 'admin', '2026-01-20 01:15:24', '[\"\\u756a\\u8304\\u6591\\u67af\\u75c5\\u53f6\", \"\\u756a\\u8304\\u6591\\u67af\\u75c5\\u53f6\", \"\\u756a\\u8304\\u6591\\u67af\\u75c5\\u53f6\", \"\\u756a\\u8304\\u6591\\u67af\\u75c5\\u53f6\"]', 'plants');

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `sex` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `tel` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `role` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `time` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'Table \'.\\demo\\user\' is marked as crashed and should be repaired' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of user
-- ----------------------------
INSERT INTO `user` VALUES (1, 'admin', 'admin', '张三', '男', '123@qq.com', '1234567889', 'admin', 'https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif', NULL);
INSERT INTO `user` VALUES (2, 'test', '12345', '张三', '男', '123@qq.com', '1234567889', 'common', 'https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif', NULL);

-- ----------------------------
-- Table structure for videorecords
-- ----------------------------
DROP TABLE IF EXISTS `videorecords`;
CREATE TABLE `videorecords`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `input_video` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `out_video` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `start_time` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `conf` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `weight` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `kind` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 101 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of videorecords
-- ----------------------------
INSERT INTO `videorecords` VALUES (98, 'http://localhost:9999/files/2dd1bd91bb6f40f5919e2dbe771c8465_生成包含牛羊动画的视频.mp4', 'http://localhost:9999/files/00941d3b7fe14a0ea9a19e58c7b0400f_output.mp4', 'test', '2026-01-20 00:36:31', '0.13', 'fire_best.pt', 'fire');
INSERT INTO `videorecords` VALUES (99, 'http://localhost:9999/files/1a9ce3f053114db3a713d5e9e0920d38_将图片生成 MP4 视频.mp4', 'http://localhost:9999/files/bc9486138a4d4de7b3945730c27a7787_output.mp4', 'admin', '2026-01-20 01:11:32', '0.11', 'plants_best.pt', 'plants');
INSERT INTO `videorecords` VALUES (100, 'http://localhost:9999/files/ff80fbcf439b4e1aac148d9f7e550a88_将图片生成 MP4 视频.mp4', 'http://localhost:9999/files/c5353339560f4cf49ce2392a7b0c574f_output.mp4', 'admin', '2026-01-20 01:15:59', '0.11', 'plants_best.pt', 'plants');

SET FOREIGN_KEY_CHECKS = 1;
