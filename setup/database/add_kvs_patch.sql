
--
-- Table structure for table `entities`
--
create table entities (
    id int not null auto_increment,
    kind      varchar(100) NOT NULL,
    PRIMARY KEY (id),
    KEY `kind_key` (`kind`)
    ) ENGINE=MyISAM DEFAULT CHARSET=latin1;


--
-- Table structure for table `attributes`
--
create table attributes (
    id int not null auto_increment,
    kind      varchar(100) NOT NULL,
    row_id    int not null,
    attribute varchar(100),
    datatype  varchar(30),
    value     mediumblob,
    PRIMARY KEY (id),
    KEY `row_id_key` (`row_id`),
    KEY `kind_key` (`kind`),
    KEY `kv` (`kind`, `attribute`, `value`(100))
    ) ENGINE=MyISAM DEFAULT CHARSET=latin1;

