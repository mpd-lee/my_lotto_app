import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(const LottoApp());
}

class LottoApp extends StatelessWidget {
  const LottoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI 로또 추천 시스템',
      theme: ThemeData(
        primarySwatch: Colors.indigo,
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<dynamic> _recommendations = [];
  bool _isLoading = false;

  Future<void> fetchRecommendations() async {
    setState(() {
      _isLoading = true;
    });

    final url = Uri.parse('http://127.0.0.1:8000/api/v1/recommend?games=5');

    try {
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _recommendations = data['recommendations'];
        });
      } else {
        _showErrorSnackBar('서버 응답 에러: ${response.statusCode}');
      }
    } catch (e) {
      _showErrorSnackBar('백엔드 서버 접속 실패! FastAPI 서버가 작동 중인지 확인해 주세요.');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.redAccent),
    );
  }

  Color _getBallColor(int number) {
    if (number <= 10) return Colors.amber.shade700;
    if (number <= 20) return Colors.blue;
    if (number <= 30) return Colors.redAccent;
    if (number <= 40) return Colors.grey.shade700;
    return Colors.green;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🎯 AI 로또 분석 추천 시스템'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            ElevatedButton.icon(
              onPressed: _isLoading ? null : fetchRecommendations,
              icon: const Icon(Icons.auto_awesome),
              label: const Text('최적 추천 번호 추출하기', style: TextStyle(fontSize: 16)),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
              ),
            ),
            const SizedBox(height: 20),
            _isLoading
                ? const Center(child: CircularProgressIndicator())
                : Expanded(
                    child: _recommendations.isEmpty
                        ? const Center(child: Text('버튼을 눌러 추천 번호를 추출해 보세요!'))
                        : ListView.builder(
                            itemCount: _recommendations.length,
                            itemBuilder: (context, index) {
                              final item = _recommendations[index];
                              final List<dynamic> nums = item['numbers'] ?? [];
                              final double score = item['score'] ?? 0.0;

                              return Card(
                                margin: const EdgeInsets.symmetric(vertical: 8),
                                child: Padding(
                                  padding: const EdgeInsets.all(12.0),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text('게임 ${index + 1} (적합도 점수: $score)',
                                          style: const TextStyle(fontWeight: FontWeight.bold)),
                                      const SizedBox(height: 10),
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                                        children: nums.map((num) {
                                          return CircleAvatar(
                                            backgroundColor: _getBallColor(num),
                                            child: Text(
                                              '$num',
                                              style: const TextStyle(
                                                color: Colors.white,
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                          );
                                        }).toList(),
                                      ),
                                    ],
                                  ),
                                ),
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