drop table if exists `stannis`.`search_history`;
drop table if exists `stannis`.`svn_diffs`;
drop table if exists `stannis`.`svn_change_path`;
drop table if exists `stannis`.`svn_log`;
drop table if exists  `stannis`.`svn_linked_change_path`; 
drop table if exists  `stannis`.`svn_module`; 

CREATE  TABLE `stannis`.`svn_log` (

  `id` INT NOT NULL AUTO_INCREMENT,

  `version` VARCHAR(45) NULL ,

  `acct_name` VARCHAR(45) NULL ,

  `date_time` DATETIME NULL ,

  `comments` TEXT NULL ,

  PRIMARY KEY (`id`) );
  
  
  CREATE  TABLE `stannis`.`svn_change_path` (

  `id` INT NOT NULL AUTO_INCREMENT ,

  `action` CHAR(1) NULL ,

  `path` MEDIUMTEXT  NULL ,
  
  `filename` VARCHAR(255) NULL ,

  `f_id` INT NULL ,

  PRIMARY KEY (`id`) ,

  INDEX `fid` (`f_id` ASC) ,

  CONSTRAINT `fid`

    FOREIGN KEY (`f_id` )

    REFERENCES `stannis`.`svn_log` (`id` )

    ON DELETE CASCADE

    ON UPDATE NO ACTION);


CREATE  TABLE `stannis`.`search_history` (

  `id` INT NOT NULL AUTO_INCREMENT ,

  `ip` VARCHAR(15) NULL COMMENT 'only ip v4' ,

  `content` VARCHAR(60) NULL COMMENT 'search content(currently only user NT name)' ,

  PRIMARY KEY (`id`) ,

  UNIQUE INDEX `id_UNIQUE` (`id` ASC) )

COMMENT = 'user search history';


CREATE  TABLE `stannis`.`svn_diffs` (

  `id` INT NOT NULL AUTO_INCREMENT ,

  `f_cp_id` INT NULL ,

  `diff` MEDIUMTEXT NULL ,

  PRIMARY KEY (`id`) ,

  INDEX `fkfk_cp_id` (`f_cp_id` ASC) ,

  CONSTRAINT `f_cp_id`

    FOREIGN KEY (`f_cp_id` )

    REFERENCES `stannis`.`svn_change_path` (`id` )

    ON DELETE CASCADE

    ON UPDATE NO ACTION)

COMMENT = 'tables store code diff html';

CREATE  TABLE `stannis`.`svn_module` (

  `id` INT NOT NULL AUTO_INCREMENT ,

  `name` VARCHAR(60) NULL ,

  `path` MEDIUMTEXT NULL ,

  `r_id` INT NULL ,

  PRIMARY KEY (`id`) )

COMMENT = 'modules(branches)/submodules releationship';

ALTER TABLE `stannis`.`svn_log` ADD COLUMN `m_id` INT NULL  AFTER `comments` , 

  ADD CONSTRAINT `m_id`

  FOREIGN KEY (`m_id` )

  REFERENCES `stannis`.`svn_module` (`id` )

  ON DELETE NO ACTION

  ON UPDATE NO ACTION

, ADD INDEX `m_id` (`m_id` ASC) ;

CREATE  TABLE `stannis`.`svn_linked_change_path` (

  `id` INT NOT NULL AUTO_INCREMENT ,

  `path` MEDIUMTEXT NULL ,

  PRIMARY KEY (`id`) );

  
ALTER TABLE `stannis`.`svn_change_path` ADD COLUMN `f_link_cp_id` INT NULL  AFTER `f_id` , 

  ADD CONSTRAINT `f_lcp_id`

  FOREIGN KEY (`f_link_cp_id` )

  REFERENCES `stannis`.`svn_linked_change_path` (`id` )

  ON DELETE NO ACTION

  ON UPDATE NO ACTION

, ADD INDEX `f_lcp_id` (`f_link_cp_id` ASC) ;