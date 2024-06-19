-- Create a new database
CREATE DATABASE deploy_test1;

-- Use the new database
USE deploy_test1;

-- Create a new table
CREATE TABLE my_deploy_table (
    id INT AUTO_INCREMENT,
    name VARCHAR(100),
    PRIMARY KEY(id)
);