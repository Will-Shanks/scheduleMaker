# README

__Required Python Libraries:__
- mysqlclient
- flask

__Setup__
1. Install python3 and pip3

2. Install python library MySQLdb and Flask
       pip3 install mysqlclient
       pip3 install flask
3. Install mysql
4. Create 'secrets.py' file in src folder that looks like:
    ```
    DBHOST="<DB IP>"
    DBUSER="<DB user>"
    DBPASSWD="<DB user password>"
    DBNAME="<DB Name>"
    ```

__Running__
1. Setup Flask app

       set FLASK_APP=src\Scheduler.py
       flask run
2. Query API
    - Choose k of ClassA classes, choose i of classB classes, etc

    - Can be Course of Section ID
    ```
     <BASEURL>/[[["CLassA1","ClassA2", ... "ClassAN"],k],[["ClassB1", "ClassB2", ... "ClassBM"],i], ... ]
    ```
    - Returns json
      ```
      [
        [
          [
            //Schedule sections
            [
              "<SectionID>",
              <Start Time in seconds>,
              <finish Time in seconds>,
              "<days class meets>"
            ],
            //more sections
            ....
          ],
          {
            //Schedule stats
            "AvgDayLen":<avg day len in hours>,
            "daysOfClass":<num days w/ class>,
            "earliestStart":<earliest start in seconds>,
            "latestFinish":<latest finish in seconds,
            "longestDay":<longest day in hours>,
            "longestGap":<longest gap between classes in hours>
            //More stats may be added
          }
        ],
        //more schedules
        ....
      ]
      ````
