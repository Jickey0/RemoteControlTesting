def WeatherGetRequest(name, value):
    return {
		"objectPath" : "/Game/Main.Main:PersistentLevel.Ultra_Dynamic_Sky_C_1",
		"access" : "WRITE_ACCESS",
		"propertyName" : name,
		"propertyValue" : {
			name : value
		}
	}
