CREATE DATABASE  IF NOT EXISTS `stannis` /*!40100 DEFAULT CHARACTER SET utf8 */;
USE `stannis`;
-- MySQL dump 10.13  Distrib 5.5.16, for Win32 (x86)
--
-- Host: localhost    Database: stannis
-- ------------------------------------------------------
-- Server version 5.5.9

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
-- Table structure for table `svn_linked_change_path`
--

DROP TABLE IF EXISTS `svn_linked_change_path`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `svn_linked_change_path` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `path` mediumtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=104 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `svn_module`
--

DROP TABLE IF EXISTS `svn_module`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `svn_module` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(60) DEFAULT NULL,
  `path` mediumtext,
  `r_id` int(11) DEFAULT NULL,
  `level` int(3) DEFAULT NULL,
  `active` int(1) DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8 COMMENT='modules(branches)/submodules releationship';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `svn_diffs`
--

DROP TABLE IF EXISTS `svn_diffs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `svn_diffs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `f_cp_id` int(11) DEFAULT NULL,
  `diff` mediumtext,
  PRIMARY KEY (`id`),
  KEY `fkfk_cp_id` (`f_cp_id`),
  CONSTRAINT `f_cp_id` FOREIGN KEY (`f_cp_id`) REFERENCES `svn_change_path` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=1809 DEFAULT CHARSET=utf8 COMMENT='tables store code diff html';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `search_history`
--

DROP TABLE IF EXISTS `search_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `search_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ip` varchar(15) DEFAULT NULL COMMENT 'only ip v4',
  `content` varchar(60) DEFAULT NULL COMMENT 'search content(currently only user NT name)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8 COMMENT='user search history';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `svn_change_path`
--

DROP TABLE IF EXISTS `svn_change_path`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `svn_change_path` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action` char(1) DEFAULT NULL,
  `path` mediumtext,
  `filename` varchar(255) DEFAULT NULL,
  `f_id` int(11) DEFAULT NULL,
  `f_link_cp_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fid` (`f_id`),
  KEY `f_lcp_id` (`f_link_cp_id`),
  CONSTRAINT `f_lcp_id` FOREIGN KEY (`f_link_cp_id`) REFERENCES `svn_linked_change_path` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fid` FOREIGN KEY (`f_id`) REFERENCES `svn_log` (`id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=2641 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `svn_log`
--

DROP TABLE IF EXISTS `svn_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `svn_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `version` varchar(45) DEFAULT NULL,
  `acct_name` varchar(45) DEFAULT NULL,
  `date_time` datetime DEFAULT NULL,
  `comments` text,
  `m_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `m_id` (`m_id`),
  CONSTRAINT `m_id` FOREIGN KEY (`m_id`) REFERENCES `svn_module` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=71 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2012-07-24  9:28:54
