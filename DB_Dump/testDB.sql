-- MySQL dump 10.13  Distrib 5.7.17, for Win64 (x86_64)
--
-- Host: localhost    Database: class_scheduler
-- ------------------------------------------------------
-- Server version	5.7.20-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `course`
--

DROP TABLE IF EXISTS `course`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `course` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(45) DEFAULT NULL,
  `code` varchar(45) DEFAULT NULL,
  `credits` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`),
  UNIQUE KEY `code_UNIQUE` (`code`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `course`
--

LOCK TABLES `course` WRITE;
/*!40000 ALTER TABLE `course` DISABLE KEYS */;
INSERT INTO `course` VALUES (4,'Beginning Hindi 2','HIND1020','5'),(5,'Algorithms','CSCI3104','4'),(6,'Principles of programing languages','CSCI3155','4'),(7,'Introduction to Data Science Algorithms','CSCI3022','3'),(8,'Experimental Physics 1','PHYS1140','1'),(9,'Introduction to Probability and Statistics','MATH3510','3');
/*!40000 ALTER TABLE `course` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `section`
--

DROP TABLE IF EXISTS `section`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `section` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `course_id` int(11) NOT NULL,
  `component` varchar(10) DEFAULT NULL,
  `section` varchar(10) DEFAULT NULL,
  `start` time(6) DEFAULT NULL,
  `finish` time(6) DEFAULT NULL,
  `days` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`),
  KEY `course_idx` (`course_id`),
  CONSTRAINT `course` FOREIGN KEY (`course_id`) REFERENCES `course` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `section`
--

LOCK TABLES `section` WRITE;
/*!40000 ALTER TABLE `section` DISABLE KEYS */;
INSERT INTO `section` VALUES (1,4,'LEC','1','10:00:00.000000','10:50:00.000000','MTWRF'),(2,5,'LEC','100','12:30:00.000000','13:45:00.000000','TR'),(3,5,'REC','101','08:00:00.000000','08:50:00.000000','W'),(4,5,'REC','102','09:00:00.000000','09:50:00.000000','W'),(5,5,'REC','103','15:00:00.000000','15:50:00.000000','W'),(6,5,'REC','104','09:00:00.000000','09:50:00.000000','F'),(7,5,'REC','105','10:00:00.000000','10:50:00.000000','F'),(8,5,'REC','106','11:00:00.000000','11:50:00.000000','F'),(9,5,'REC','107','12:00:00.000000','12:50:00.000000','F'),(11,5,'LEC','200','09:30:00.000000','10:45:00.000000','TR'),(12,5,'LEC','200B',NULL,NULL,'ONLINE'),(13,5,'REC','201','16:00:00.000000','16:50:00.000000','W'),(14,5,'REC','202','17:00:00.000000','17:50:00.000000','W'),(15,5,'REC','203','13:00:00.000000','13:50:00.000000','F'),(16,5,'REC','204','14:00:00.000000','14:50:00.000000','F'),(17,5,'REC','205','16:00:00.000000','16:50:00.000000','W'),(18,5,'REC','206','17:00:00.000000','17:50:00.000000','W'),(19,5,'REC','207','13:00:00.000000','13:50:00.000000','F'),(20,5,'REC','208','14:00:00.000000','14:50:00.000000','F'),(21,6,'LEC','100','11:00:00.000000','12:15:00.000000','TR'),(22,6,'REC','101','13:00:00.000000','13:50:00.000000','T'),(23,6,'REC','102','15:00:00.000000','15:50:00.000000','T'),(24,6,'REC','103','16:00:00.000000','16:50:00.000000','T'),(25,6,'REC','104','08:00:00.000000','08:50:00.000000','W'),(26,6,'REC','105','16:00:00.000000','16:50:00.000000','W'),(27,6,'REC','106','17:00:00.000000','17:50:00.000000','W'),(28,7,'LEC','001','10:00:00.000000','10:50:00.000000','MWF'),(29,8,'LEC','100','16:00:00.000000','16:50:00.000000','M'),(30,8,'LEC','200','16:00:00.000000','16:50:00.000000','T'),(31,9,'LEC','001','09:00:00.000000','09:50:00.000000','MWF');
/*!40000 ALTER TABLE `section` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-10-22 17:38:55
