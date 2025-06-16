import 'package:flutter/material.dart';
import 'package:pie_chart/pie_chart.dart';
import 'dart:math';

class AnalyticsScreen extends StatefulWidget {
  const AnalyticsScreen({super.key});

  @override
  State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen> {
  List<Map<String, dynamic>> tasks = [
    {"category": "Social Media", "percentage": "18"},
    {"category": "Working", "percentage": "52"},
    {"category": "Nothing", "percentage": "30"},
  ];

  List<Map<String, dynamic>> timeStamps = [
    {"category": "Social media", "time_spent": "7:25:52"},
    {"category": "Working", "time_spent": "2:14:00"},
    {"category": "Nothing", "time_spent": "1:15:25"},
  ];

  Map<String, String> get timemap {
    Map<String, String> time = {};
    for (var task in timeStamps) {
      time[task["category"]] = task["time_spent"];
    }
    return time;
  }

  Map<String, double> get dataMap {
    Map<String, double> map = {};
    for (var task in tasks) {
      map[task["category"]] = double.parse(task["percentage"]);
    }
    return map;
  }

  List<Color> get colorList {
    Random random = Random();
    return List.generate(
      tasks.length,
      (_) => Color.fromARGB(
        255,
        random.nextInt(200),
        random.nextInt(200),
        random.nextInt(200),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final screenHeight = MediaQuery.of(context).size.height;
    final screenWidth = MediaQuery.of(context).size.width;

    return Scaffold(
      backgroundColor: const Color(0xFF181026),
      appBar: AppBar(
        backgroundColor: const Color(0xFF2C1A3A),
        title: const Text(
          'Analytics Page',
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.white),
        ),
      ),
      body: Padding(
        padding: EdgeInsets.symmetric(
          horizontal: screenWidth * 0.03,
          vertical: screenHeight * 0.05,
        ),
        child: Column(
          children: [
            PieChart(
              dataMap: dataMap,
              colorList: colorList,
              chartRadius: screenWidth / 2,
              ringStrokeWidth: 24,
              animationDuration: const Duration(seconds: 2),
              chartValuesOptions: const ChartValuesOptions(
                showChartValues: false,
                showChartValuesOutside: false,
                showChartValuesInPercentage: false,
                showChartValueBackground: true,
              ),
              legendOptions: LegendOptions(
                showLegends: true,
                legendTextStyle: TextStyle(color: Colors.white),
              ),
            ),
            SizedBox(height: screenHeight * 0.1),
            SizedBox(
              height:
                  screenHeight * 0.45, // Adjustable based on your layout needs
              child: ListView.separated(
                itemCount: tasks.length,
                separatorBuilder: (_, __) => const SizedBox(height: 25),
                itemBuilder: (context, index) {
                  final item = tasks[index];
                  final time_item = timeStamps[index];
                  final color = colorList[index % colorList.length];
                  return Row(
                    children: [
                      Container(
                        width: 12,
                        height: 12,
                        decoration: BoxDecoration(
                          color: color,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          item['category'],
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 15,
                          ),
                        ),
                      ),

                      Text(
                        time_item['time_spent'],
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 15,
                        ),
                      ),
                      const Spacer(flex: 1),
                      Text(
                        '${item['percentage']}%',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 15,
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
