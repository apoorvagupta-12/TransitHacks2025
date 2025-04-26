# Create borough table
CREATE TABLE .users (
 user_id				INT UNSIGNED NOT NULL AUTO_INCREMENT
,first_name				VARCHAR(20) NOT NULL
,last_name				VARCHAR(20) NOT NULL
,date_of_birth			DATE NOT NULL # SPECIFY THAT IT MUST BE MORE THAN A CERTAIN AGE! -- THIS CAN COME FROM CNET EVENTUALLY
,sex					ENUM('MALE', 'FEMALE', 'INTERSEX') NOT NULL
,email					VARCHAR(40) NOT NULL
,phone_number			BIGINT NOT NULL
#,uc_affiliation 		ENUM() NOT NULL # from list
,undergrad 				TINYINT NOT NULL
,interests_sports		TINYINT NOT NULL
,interests_politics		TINYINT NOT NULL
,interests_marxism		TINYINT NOT NULL
,interests_trains		TINYINT NOT NULL
,interests_computers	TINYINT NOT NULL 
,interests_turtles		TINYINT NOT NULL
,interests_life			TINYINT NOT NULL
,interests_death		TINYINT	NOT NULL
#,image					VARCHAR(MAX)
,instagram 				VARCHAR(100) # OPTIONAL LINK
,facebook 				VARCHAR(100) # OPTIONAL LINK
,twitter 				VARCHAR(100) # OPTIONAL LINK
,PRIMARY KEY(user_id, email)
) ;

CREATE TABLE .stations (
 station_id				BIGINT UNSIGNED NOT NULL AUTO_INCREMENT
,station_name			VARCHAR(100)
,PRIMARY KEY(station_id)
) ;

CREATE TABLE .requests (
 request_id			BIGINT UNSIGNED NOT NULL AUTO_INCREMENT	
,user_id			INT UNSIGNED NOT NULL
,orig_station_id	BIGINT NOT NULL
,dest_station_id	BIGINT NOT NULL
,window_start		DATETIME NOT NULL
,window_end			DATETIME NOT NULL
,status				ENUM('CANCELLED', 'ACTIVE', 'COMPLETED') NOT NULL # 'CANCELLED', 'ACTIVE', 'COMPLETED'
,PRIMARY KEY(request_id)
,CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES .users(user_id)
,CONSTRAINT fk_orig_station_id FOREIGN KEY (orig_station_id) REFERENCES .stations(station_id)
,CONSTRAINT fk_dest_station_id FOREIGN KEY (dest_station_id) REFERENCES .stations(station_id)
) ;

CREATE TABLE .schedule (
 station_id			BIGINT UNSIGNED NOT NULL
,run_id				INT UNSIGNED NOT NULL
,arrival_time		DATETIME
,PRIMARY KEY(station_id, run_id)
,CONSTRAINT fk_station_id FOREIGN KEY (station_id) REFERENCES .stations(station_id)
) ;

CREATE TABLE .match ( 
 match_id			BIGINT UNSIGNED NOT NULL AUTO_INCREMENT
,user_a_id 			INT UNSIGNED NOT NULL
,user_b_id			INT UNSIGNED NOT NULL
,orig_station_id	INT UNSIGNED NOT NULL
,dest_station_id	INT UNSIGNED NOT NULL
,run_id				INT UNSIGNED NOT NULL			
,PRIMARY KEY(trip_id)
,CONSTRAINT fk_user_a_id FOREIGN KEY (user_a_id) REFERENCES .users(user_id)
,CONSTRAINT fk_user_b_id FOREIGN KEY (user_b_id) REFERENCES .users(user_id)
,CONSTRAINT fk_orig_station_id FOREIGN KEY (orig_station_id) REFERENCES .stations(station_id)
,CONSTRAINT fk_dest_station_id FOREIGN KEY (dest_station_id) REFERENCES .stations(station_id)
) ;