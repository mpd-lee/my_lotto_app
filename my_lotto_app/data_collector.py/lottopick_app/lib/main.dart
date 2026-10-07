import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const LottoPickApp());
}

class LottoPickApp extends StatelessWidget {
  const LottoPickApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '로또픽',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0D1B2A)),
        useMaterial3: true,
      ),
      home: const LottoWebView(),
      // 오른쪽 상단 디버그 띠 제거
      debugShowCheckedModeBanner: false, 
    );
  }
}

class LottoWebView extends StatefulWidget {
  const LottoWebView({super.key});

  @override
  State<LottoWebView> createState() => _LottoWebViewState();
}

class _LottoWebViewState extends State<LottoWebView> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();
    
    // 웹뷰 컨트롤러 초기화 및 설정 (대표님의 Streamlit 주소 적용 완료!)
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0xFF0D1B2A))
      ..loadRequest(
        Uri.parse('https://mylottoapp-3mygrnqs6j7ard8n3zrvj9.streamlit.app/'),
      );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1B2A),
      body: SafeArea(
        child: WebViewWidget(controller: _controller),
      ),
    );
  }
}