CREATE USER 'viewer_user'@'localhost' IDENTIFIED BY 'viewer123';
CREATE USER 'editor_user'@'localhost' IDENTIFIED BY 'editor123';
CREATE USER 'dba_user'@'localhost' IDENTIFIED BY 'dba123';

GRANT SELECT ON zmart.* TO 'viewer_user'@'localhost';
GRANT SELECT, UPDATE ON zmart.* TO 'editor_user'@'localhost';
GRANT ALL PRIVILEGES ON zmart.* TO 'dba_user'@'localhost';
GRANT CREATE USER ON *.* TO 'dba_user'@'localhost' WITH GRANT OPTION;

FLUSH PRIVILEGES;
