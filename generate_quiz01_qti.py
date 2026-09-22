#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas LMS QTI 1.2 Quiz Package Generator
第1回「プログラムとは」小テスト生成スクリプト
"""

import html
import io
import os
import uuid
import zipfile

QUIZ_TITLE = "第1回小テスト：プログラムとは"
QUIZ_DESC = "<p>第1回「プログラムとは」の理解度確認小テストです。<br>5つのトピックからそれぞれランダムに1問が出題されます（計5問、各1点 / 5点満点）。</p>"

# 各トピック（問題グループ）と問題の定義
TOPICS = [
    {
        "group_id": "group_1",
        "title": "コンピュータの構成と動作（CPUと記憶装置）",
        "pick": 1,
        "points_per_item": 1.0,
        "questions": [
            {
                "id": "q1_1",
                "title": "問題 1-1（主記憶と補助記憶の違い）",
                "prompt": "<p>コンピュータの主記憶（メインメモリ）と補助記憶（SSD/HDD）の違いに関する説明として、<strong>正しいもの</strong>を1つ選んでください。</p>",
                "answers": [
                    ("主記憶は不揮発性であり、電源を切ってもデータが消えることはない。", False),
                    ("プログラム実行時、CPUは補助記憶から直接ではなく、主記憶に読み込まれた命令を1個ずつ取り出して実行する。", True),
                    ("補助記憶は主記憶に比べてアクセス速度が数十倍から数千倍高速である。", False),
                    ("主記憶にはOSや写真・動画ファイルが永続的に保存される。", False),
                ],
                "explanation": "<p><b>【解説】</b><br>主記憶（メインメモリ）は高速ですが揮発性（電源OFFで消去）です。プログラムを実行する際は、まず補助記憶から主記憶にプログラムがコピーされ、CPUは主記憶から命令を読み込んで実行します。</p>"
            },
            {
                "id": "q1_2",
                "title": "問題 1-2（CPUの構成部）",
                "prompt": "<p>コンピュータの頭脳であるCPU（中央演算処理装置）を構成する主な2つの機能部として、<strong>適切な組み合わせ</strong>を1つ選んでください。</p>",
                "answers": [
                    ("入力部 と 出力部", False),
                    ("制御部 と 演算部", True),
                    ("主記憶部 と 補助記憶部", False),
                    ("翻訳部 と 実行部", False),
                ],
                "explanation": "<p><b>【解説】</b><br>CPUは主に、計算や値の比較を行う「演算部（ALU）」と、メモリから命令を取り出して解読・指示を送る「制御部」から構成されています。</p>"
            },
            {
                "id": "q1_3",
                "title": "問題 1-3（機械語の特徴）",
                "prompt": "<p>CPUが直接理解して実行できる「機械語（マシン語）」に関する説明として、<strong>最も適切なもの</strong>を1つ選んでください。</p>",
                "answers": [
                    ("人間が日常的に話す英語に近い単語で書かれたプログラムである。", False),
                    ("世界中のすべてのCPUで共通規格となっており、どのコンピュータでもそのまま動く。", False),
                    ("<code>0</code> と <code>1</code> のビット列（数値）で表現された命令であり、CPUの種類（アーキテクチャ）ごとに仕様が異なる。", True),
                    ("Pythonなどのスクリプト言語のコードそのもののことである。", False),
                ],
                "explanation": "<p><b>【解説】</b><br>機械語は <code>0</code> と <code>1</code> の並びで表現されており、CPUの種類（x86_64、ARMなど）によって仕様が異なります。人間にとって読み書きが難しいため、Pythonなどの高水準言語が生まれました。</p>"
            }
        ]
    },
    {
        "group_id": "group_2",
        "title": "プログラミング言語",
        "pick": 1,
        "points_per_item": 1.0,
        "questions": [
            {
                "id": "q2_1",
                "title": "問題 2-1（制御構造の3要素）",
                "prompt": "<p>高校「情報I」でも扱われた、アルゴリズムを組み立てる<strong>基本の3つの制御構造</strong>の組み合わせとして、正しいものを1つ選んでください。</p>",
                "answers": [
                    ("入力、計算、出力", False),
                    ("順次、分岐、反復", True),
                    ("定義、代入、参照", False),
                    ("コンパイル、実行、デバッグ", False),
                ],
                "explanation": "<p><b>【解説】</b><br>あらゆるプログラムは「順次（上から順に実行）」「分岐（条件によって分ける）」「反復（同じ処理を繰り返す）」という3つの基本構造の組み合わせで記述できます。</p>"
            },
            {
                "id": "q2_2",
                "title": "問題 2-2（高水準言語と機械語）",
                "prompt": "<p>人間が記述する「高水準言語（プログラミング言語）」と、コンピュータが処理する「機械語」の関係についての説明として、<strong>最も適切なもの</strong>を1つ選んでください。</p>",
                "answers": [
                    ("CPUは高水準言語で書かれた英単語を直接解読してそのまま実行できる。", False),
                    ("高水準言語は機械語よりもコンピュータが高速に処理できるように作られたものである。", False),
                    ("人間が書いた高水準言語のコード（ソースコード）は、翻訳ソフトウェア（インタプリタやコンパイラ）によって機械語に変換されてから実行される。", True),
                    ("現在のコンピュータでは機械語は一切使われておらず、高水準言語のみで動作している。", False),
                ],
                "explanation": "<p><b>【解説】</b><br>CPUが解釈できるのは <code>0</code> と <code>1</code> の機械語のみです。人間が理解しやすい英単語や数式で書いたソースコードは、翻訳ソフトウェアによって機械語に変換されて初めて実行されます。</p>"
            },
            {
                "id": "q2_3",
                "title": "問題 2-3（プログラミング言語の多様性）",
                "prompt": "<p>「世界共通のプログラミング言語が1つだけではなく、多種多様な言語が存在している理由」に関する説明として、<strong>最も適切なもの</strong>を1つ選んでください。</p>",
                "answers": [
                    ("時代とともに古い言語の文法がすべて使えなくなるため、毎年新しい言語を作り直しているから。", False),
                    ("コンピュータのメーカー各社が自社製品以外でプログラムを動かせないように囲い込んでいるから。", False),
                    ("ハードウェアの高速制御、Webブラウザ上の動作、データ分析など、解決したい目的や用途によって言語の得意分野が異なるから。", True),
                    ("英語圏、アジア圏、ヨーロッパ圏など、話されている母国語ごとにプログラミング言語が分かれているから。", False),
                ],
                "explanation": "<p><b>【解説】</b><br>大工道具にノコギリや金づちがあるように、プログラミング言語にも「高速動作が得意（C言語等）」「Webブラウザで動く（JavaScript等）」「データ分析・機械学習が手軽（Python等）」といった適材適所のトレードオフがあります。</p>"
            }
        ]
    },
    {
        "group_id": "group_3",
        "title": "Pythonの特徴と実行形態",
        "pick": 1,
        "points_per_item": 1.0,
        "questions": [
            {
                "id": "q3_1",
                "title": "問題 3-1（インタプリタ型言語）",
                "prompt": "<p>Pythonが<strong>「インタプリタ型言語」</strong>であることのメリット・特徴として、最も適切なものを1つ選んでください。</p>",
                "answers": [
                    ("実行前にプログラム全体を一括して機械語に変換する長い待ち時間が必要である。", False),
                    ("プログラムを1行ずつ解釈しながら対話的に実行できるため、試行錯誤やデータの確認がしやすい。", True),
                    ("プログラムにエラーが含まれていても、エラーを自動的に修正して実行を継続してくれる。", False),
                    ("他のどのプログラミング言語よりもコンピュータの実行速度（計算速度）が極限まで速い。", False),
                ],
                "explanation": "<p><b>【解説】</b><br>インタプリタ型言語であるPythonは、コードを1行ずつ解釈しながら対話的・即時的に実行できます。これにより、初学者の学習や試行錯誤、データ分析に非常に適しています。</p>"
            },
            {
                "id": "q3_2",
                "title": "問題 3-2（Pythonの特徴・誤り選択）",
                "prompt": "<p>Python言語の特徴に関する説明として、<strong>誤っているもの</strong>を1つ選んでください。</p>",
                "answers": [
                    ("シンプルで読みやすい文法設計になっており、コードの可読性が高い。", False),
                    ("数値計算、データ分析、機械学習などの強力なライブラリ群が世界中で豊富に提供されている。", False),
                    ("インタプリタ型言語であり、コードを1行ずつ解釈しながら対話的に実行して結果を確認できる。", False),
                    ("コンピュータのCPUが翻訳ソフトウェア（インタプリタ等）を通さずに直接理解・実行できる。", True),
                ],
                "explanation": "<p><b>【解説】</b><br>CPUが翻訳なしで直接実行できるのは <code>0</code> と <code>1</code> で書かれた「機械語」のみです。Pythonは人間が理解しやすい高水準言語であるため、実行にはインタプリタによる機械語への翻訳が必要です。</p>"
            },
            {
                "id": "q3_3",
                "title": "問題 3-3（対話型シェルとスクリプトファイル）",
                "prompt": "<p>Pythonプログラムを実行する「対話型シェル（REPL）」と「スクリプトファイル（.pyファイル）」の使い分けに関する説明として、<strong>最も適切なもの</strong>を1つ選んでください。</p>",
                "answers": [
                    ("対話型シェルに一度入力したコードは自動的にファイルとして永久保存されるため、本格的な開発はすべて対話型シェルで行う。", False),
                    ("関数の挙動確認や簡単な計算には対話型シェルが便利であり、まとまった一連の処理を作成する場合はスクリプトファイルに保存して実行する。", True),
                    ("スクリプトファイルには <code>print()</code> 関数を書くことができず、計算処理しか記述できない。", False),
                    ("対話型シェルとスクリプトファイルでは、使用できるPythonの文法が完全に異なる。", False),
                ],
                "explanation": "<p><b>【解説】</b><br><code>&gt;&gt;&gt; </code> が表示される対話型シェルはその場での簡易確認や実験に適しており、まとまったプログラムはエディタ等で <code>.py</code> ファイルに記述・保存して実行します。</p>"
            }
        ]
    },
    {
        "group_id": "group_4",
        "title": "基本文法と変数・演算子",
        "pick": 1,
        "points_per_item": 1.0,
        "questions": [
            {
                "id": "q4_1",
                "title": "問題 4-1（代入文の意味）",
                "prompt": "<p>Pythonにおけるプログラミングの「代入文」<code>x = 10</code> の意味として、<strong>最も適切なもの</strong>を1つ選んでください。</p>",
                "answers": [
                    ("数学の方程式と同じく、「x と 10 が等しい」という状態を表している。", False),
                    ("右辺の値（10）を、左辺の変数（x）という名前の記憶領域に格納する。", True),
                    ("変数 x の中身を空にして、新しく 10 という名前の変数を作る。", False),
                    ("画面に「x = 10」という文字列を出力する。", False),
                ],
                "explanation": "<p><b>【解説】</b><br>プログラミングにおける <code>=</code> は等号ではなく「代入演算子」です。「右辺の計算結果や値を左辺の変数に入れる」という操作を意味します。</p>"
            },
            {
                "id": "q4_2",
                "title": "問題 4-2（変数値の更新）",
                "prompt": "<p>以下のPythonプログラムを実行したとき、画面に出力される値として<strong>正しいもの</strong>を1つ選んでください。</p><pre><code>count = 5\ncount = count + 3\ncount = count * 2\nprint(count)</code></pre>",
                "answers": [
                    ("5", False),
                    ("8", False),
                    ("16", True),
                    ("11", False),
                ],
                "explanation": "<p><b>【解説】</b><br>最初 <code>count</code> に 5 が代入されます。次に <code>5 + 3</code> の結果である 8 が上書き代入され、最後に <code>8 * 2</code> の結果である 16 が代入されて出力されます。</p>"
            },
            {
                "id": "q4_3",
                "title": "問題 4-3（変数名の命名規則）",
                "prompt": "<p>Pythonで<strong>変数名</strong>として使用したとき、文法エラーにならず<strong>正しく使える名前</strong>を1つ選んでください。</p>",
                "answers": [
                    ("<code>2nd_total</code> （先頭が数字）", False),
                    ("<code>user_score</code> （アルファベットとアンダースコア）", True),
                    ("<code>total score</code> （途中に半角スペースを含む）", False),
                    ("<code>user-name</code> （引き算記号のハイフンを含む）", False),
                ],
                "explanation": "<p><b>【解説】</b><br>変数名に使える文字はアルファベット・数字・アンダースコア <code>_</code> です。ただし先頭の文字に数字を使うことはできません（Aは不可）。またスペース（C）や演算子記号（D）も含めることはできません。</p>"
            },
            {
                "id": "q4_4",
                "title": "問題 4-4（空白とコメントのルール）",
                "prompt": "<p>Pythonプログラムにおける「空白（スペース）」や「コメント」のルールに関する説明として、<strong>誤っているもの</strong>を1つ選んでください。</p>",
                "answers": [
                    ("<code>#</code> 記号からその行の末尾まではコメントとなり、コンピュータは実行時にこれを無視する。", False),
                    ("プログラムコードの途中に全角スペース（日本語入力の空白）が紛れ込むと、文法エラー（<code>SyntaxError</code>）の原因になる。", False),
                    ("<code>+</code> や <code>=</code> などの演算子の前後に半角スペースを空けて記述しても、文法エラーにはならず正しく実行される。", False),
                    ("<code>#</code> で始まるコメントはプログラムの最初の1行目にしか書くことができず、コードと同じ行の右側に書くことはできない。", True),
                ],
                "explanation": "<p><b>【解説】</b><br>コメント記号 <code>#</code> は行の先頭だけでなく、コードの途中（行末）にも書くことができます（例：<code>count = 5  # 初期値を設定</code>）。</p>"
            }
        ]
    },
    {
        "group_id": "group_5",
        "title": "関数とモジュール",
        "pick": 1,
        "points_per_item": 1.0,
        "questions": [
            {
                "id": "q5_1",
                "title": "問題 5-1（関数定義キーワード）",
                "prompt": "<p>Pythonで新しく独自の関数を定義するときに使用するキーワードとして、<strong>正しいもの</strong>を1つ選んでください。</p>",
                "answers": [
                    ("<code>function</code>", False),
                    ("<code>def</code>", True),
                    ("<code>define</code>", False),
                    ("<code>func</code>", False),
                ],
                "explanation": "<p><b>【解説】</b><br>Pythonでの関数定義は <code>def 関数名(引数):</code> という書式で記述します。</p>"
            },
            {
                "id": "q5_2",
                "title": "問題 5-2（関数の引数と戻り値）",
                "prompt": "<p>以下のPythonプログラムを実行したときに出力される結果として、<strong>正しいもの</strong>を1つ選んでください。</p><pre><code>def calc(x):\n    return x * 3 + 1\n\nans = calc(4)\nprint(ans)</code></pre>",
                "answers": [
                    ("7", False),
                    ("13", True),
                    ("12", False),
                    ("calc(4)", False),
                ],
                "explanation": "<p><b>【解説】</b><br>引数 <code>x</code> に <code>4</code> が渡され、関数内で <code>4 * 3 + 1 = 13</code> が計算されて <code>return</code> で返されます。それが変数 <code>ans</code> に代入されて表示されます。</p>"
            },
            {
                "id": "q5_3",
                "title": "問題 5-3（モジュールの利用）",
                "prompt": "<p>Pythonで標準モジュール <code>math</code> を読み込み、そこに含まれる円周率の値 <code>pi</code> を使いたいときの記述方法として、<strong>最も適切なもの</strong>を1つ選んでください。</p>",
                "answers": [
                    ("<pre><code>load math\nprint(pi)</code></pre>", False),
                    ("<pre><code>import math\nprint(math.pi)</code></pre>", True),
                    ("<pre><code>using math\nprint(math-&gt;pi)</code></pre>", False),
                    ("<pre><code>include &lt;math.h&gt;\nprint(math:pi)</code></pre>", False),
                ],
                "explanation": "<p><b>【解説】</b><br>Pythonではモジュールを取り込むために <code>import モジュール名</code> を使い、その中の関数や定数には <code>モジュール名.要素名</code> とドットで繋いでアクセスします。</p>"
            },
            {
                "id": "q5_4",
                "title": "問題 5-4（組み込み関数lenとmax）",
                "prompt": "<p>組み込み関数 <code>len()</code> と <code>max()</code> の使い方に関する説明として、<strong>正しいもの</strong>を1つ選んでください。</p>",
                "answers": [
                    ("<code>len(\"Python\")</code> は文字列を大文字に変換する。", False),
                    ("<code>len(\"Keio SFC\")</code> は文字列の文字数を返し、<code>max(3, 5, 1)</code> は与えられた引数の中で最大値を返す。", True),
                    ("<code>max()</code> 関数は引数を必ず2つしか指定できない。", False),
                    ("<code>len()</code> 関数は変数のメモリ使用量（バイト数）を調べる関数である。", False),
                ],
                "explanation": "<p><b>【解説】</b><br><code>len()</code> は文字列の長さ（文字数）を返し、<code>max()</code> は渡された複数の引数の中から最も大きい値を返します。</p>"
            }
        ]
    }
]


def build_qti_xml(assessment_id, topics):
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.imsglobal.org/xsd/ims_qtiasiv1p2 http://www.imsglobal.org/xsd/ims_qtiasiv1p2p1.xsd">',
        f'  <assessment ident="{assessment_id}" title="{html.escape(QUIZ_TITLE)}">',
        '    <qtimetadata>',
        '      <qtimetadatafield>',
        '        <fieldlabel>cc_maxattempts</fieldlabel>',
        '        <fieldentry>1</fieldentry>',
        '      </qtimetadatafield>',
        '    </qtimetadata>',
        '    <section ident="root_section">'
    ]

    for topic in topics:
        group_id = topic["group_id"]
        group_title = html.escape(topic["title"])
        pick = topic["pick"]
        pts = topic["points_per_item"]

        xml.append(f'      <section ident="{group_id}" title="{group_title}">')
        xml.append('        <selection_ordering>')
        xml.append('          <selection>')
        xml.append(f'            <selection_number>{pick}</selection_number>')
        xml.append('            <selection_extension>')
        xml.append(f'              <points_per_item>{pts:.1f}</points_per_item>')
        xml.append('            </selection_extension>')
        xml.append('          </selection>')
        xml.append('        </selection_ordering>')

        for q in topic["questions"]:
            qid = q["id"]
            qtitle = html.escape(q["title"])
            prompt = q["prompt"]
            ans_tuples = q["answers"]
            explanation = q.get("explanation", "")

            # 選択肢ID生成
            ans_ids = [f"{qid}_ans_{i}" for i in range(len(ans_tuples))]
            correct_ans_id = None
            for idx, (_, is_corr) in enumerate(ans_tuples):
                if is_corr:
                    correct_ans_id = ans_ids[idx]
                    break

            orig_ans_str = ",".join(ans_ids)

            xml.append(f'        <item ident="{qid}" title="{qtitle}">')
            xml.append('          <itemmetadata>')
            xml.append('            <qtimetadata>')
            xml.append('              <qtimetadatafield>')
            xml.append('                <fieldlabel>question_type</fieldlabel>')
            xml.append('                <fieldentry>multiple_choice_question</fieldentry>')
            xml.append('              </qtimetadatafield>')
            xml.append('              <qtimetadatafield>')
            xml.append('                <fieldlabel>points_possible</fieldlabel>')
            xml.append(f'                <fieldentry>{pts:.1f}</fieldentry>')
            xml.append('              </qtimetadatafield>')
            xml.append('              <qtimetadatafield>')
            xml.append('                <fieldlabel>original_answer_ids</fieldlabel>')
            xml.append(f'                <fieldentry>{orig_ans_str}</fieldentry>')
            xml.append('              </qtimetadatafield>')
            xml.append('              <qtimetadatafield>')
            xml.append('                <fieldlabel>assessment_question_identifierref</fieldlabel>')
            xml.append(f'                <fieldentry>{qid}_ref</fieldentry>')
            xml.append('              </qtimetadatafield>')
            xml.append('            </qtimetadata>')
            xml.append('          </itemmetadata>')
            xml.append('          <presentation>')
            xml.append('            <material>')
            xml.append(f'              <mattext texttype="text/html"><![CDATA[{prompt}]]></mattext>')
            xml.append('            </material>')
            xml.append('            <response_lid ident="response1" rcardinality="Single">')
            xml.append('              <render_choice>')

            for a_id, (a_text, _) in zip(ans_ids, ans_tuples):
                xml.append(f'                <response_label ident="{a_id}">')
                xml.append('                  <material>')
                xml.append(f'                    <mattext texttype="text/html"><![CDATA[{a_text}]]></mattext>')
                xml.append('                  </material>')
                xml.append('                </response_label>')

            xml.append('              </render_choice>')
            xml.append('            </response_lid>')
            xml.append('          </presentation>')
            xml.append('          <resprocessing>')
            xml.append('            <outcomes>')
            xml.append('              <decvar maxvalue="100" minvalue="0" varname="SCORE" vartype="Decimal"/>')
            xml.append('            </outcomes>')
            xml.append('            <respcondition continue="No">')
            xml.append('              <conditionvar>')
            xml.append(f'                <varequal respident="response1">{correct_ans_id}</varequal>')
            xml.append('              </conditionvar>')
            xml.append(f'              <setvar action="Set" varname="SCORE">{pts:.1f}</setvar>')
            xml.append('              <displayfeedback feedbacktype="Response" linkrefid="general_fb"/>')
            xml.append('            </respcondition>')
            xml.append('            <respcondition continue="Yes">')
            xml.append('              <conditionvar>')
            xml.append('                <other/>')
            xml.append('              </conditionvar>')
            xml.append('              <displayfeedback feedbacktype="Response" linkrefid="general_fb"/>')
            xml.append('            </respcondition>')
            xml.append('          </resprocessing>')
            if explanation:
                xml.append('          <itemfeedback ident="general_fb">')
                xml.append('            <flow_mat>')
                xml.append('              <material>')
                xml.append(f'                <mattext texttype="text/html"><![CDATA[{explanation}]]></mattext>')
                xml.append('              </material>')
                xml.append('            </flow_mat>')
                xml.append('          </itemfeedback>')
            xml.append('        </item>')

        xml.append('      </section>')

    xml.append('    </section>')
    xml.append('  </assessment>')
    xml.append('</questestinterop>')

    return "\n".join(xml)


def build_assessment_meta_xml(assessment_id, assignment_id, topics):
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<quiz identifier="{assessment_id}" xmlns="http://canvas.instructure.com/xsd/cccv1p0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd">',
        f'  <title>{html.escape(QUIZ_TITLE)}</title>',
        f'  <description>{html.escape(QUIZ_DESC)}</description>',
        '  <shuffle_answers>true</shuffle_answers>',
        '  <scoring_policy>keep_highest</scoring_policy>',
        '  <hide_results></hide_results>',
        '  <quiz_type>assignment</quiz_type>',
        '  <points_possible>5.0</points_possible>',
        '  <require_lockdown_browser>false</require_lockdown_browser>',
        '  <require_lockdown_browser_for_results>false</require_lockdown_browser_for_results>',
        '  <require_lockdown_browser_monitor>false</require_lockdown_browser_monitor>',
        '  <lockdown_browser_monitor_data/>',
        '  <show_correct_answers>true</show_correct_answers>',
        '  <anonymous_submissions>false</anonymous_submissions>',
        '  <could_be_locked>false</could_be_locked>',
        '  <allowed_attempts>1</allowed_attempts>',
        '  <one_question_at_a_time>false</one_question_at_a_time>',
        '  <cant_go_back>false</cant_go_back>',
        '  <available>true</available>',
        '  <one_time_results>false</one_time_results>',
        '  <show_correct_answers_last_attempt>false</show_correct_answers_last_attempt>',
        '  <only_visible_to_overrides>false</only_visible_to_overrides>',
        '  <module_locked>false</module_locked>',
        '  <quiz_groups>'
    ]

    for topic in topics:
        gid = topic["group_id"]
        gtitle = html.escape(topic["title"])
        pick = topic["pick"]
        pts = topic["points_per_item"]
        xml.append(f'    <quiz_group identifier="{gid}">')
        xml.append(f'      <title>{gtitle}</title>')
        xml.append(f'      <question_points>{pts:.1f}</question_points>')
        xml.append(f'      <pick_count>{pick}</pick_count>')
        xml.append('    </quiz_group>')

    xml.extend([
        '  </quiz_groups>',
        f'  <assignment_group_identifierref>assignment_group_{assessment_id}</assignment_group_identifierref>',
        f'  <assignment identifier="{assignment_id}">',
        f'    <title>{html.escape(QUIZ_TITLE)}</title>',
        '    <due_at/>',
        '    <lock_at/>',
        '    <unlock_at/>',
        '    <module_locked>false</module_locked>',
        '    <workflow_state>published</workflow_state>',
        '    <assignment_overrides/>',
        f'    <quiz_identifierref>{assessment_id}</quiz_identifierref>',
        '    <allowed_extensions/>',
        '    <has_group_category>false</has_group_category>',
        '    <points_possible>5.0</points_possible>',
        '    <grading_type>points</grading_type>',
        '    <all_day>false</all_day>',
        '    <submission_types>online_quiz</submission_types>',
        '    <position>1</position>',
        '    <turnitin_enabled>false</turnitin_enabled>',
        '    <vericite_enabled>false</vericite_enabled>',
        '    <peer_review_count>0</peer_review_count>',
        '    <peer_reviews>false</peer_reviews>',
        '    <automatic_peer_reviews>false</automatic_peer_reviews>',
        '    <anonymous_peer_reviews>false</anonymous_peer_reviews>',
        '    <grade_group_students_individually>false</grade_group_students_individually>',
        '    <freeze_on_copy>false</freeze_on_copy>',
        '    <omit_from_final_grade>false</omit_from_final_grade>',
        '    <intra_group_peer_reviews>false</intra_group_peer_reviews>',
        '  </assignment>',
        '</quiz>'
    ])
    return "\n".join(xml)


def build_manifest_xml(manifest_id, assessment_id, meta_dep_id):
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<manifest identifier="{manifest_id}" xmlns="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1" xmlns:lom="http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource" xmlns:imsmd="http://www.imsglobal.org/xsd/imsmd_v1p2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1 http://www.imsglobal.org/xsd/imscp_v1p1.xsd http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource http://www.imsglobal.org/profile/cc/ccv1p1/LOM/ccv1p1_lomresource_v1p0.xsd http://www.imsglobal.org/xsd/imsmd_v1p2 http://www.imsglobal.org/xsd/imsmd_v1p2p2.xsd">',
        '  <metadata>',
        '    <schema>IMS Content</schema>',
        '    <schemaversion>1.1.3</schemaversion>',
        '    <imsmd:lom>',
        '      <imsmd:general>',
        '        <imsmd:title>',
        f'          <imsmd:string>{html.escape(QUIZ_TITLE)}</imsmd:string>',
        '        </imsmd:title>',
        '      </imsmd:general>',
        '    </imsmd:lom>',
        '  </metadata>',
        '  <organizations/>',
        '  <resources>',
        f'    <resource identifier="{assessment_id}" type="imsqti_xmlv1p2">',
        f'      <file href="{assessment_id}/{assessment_id}.xml"/>',
        f'      <dependency identifierref="{meta_dep_id}"/>',
        '    </resource>',
        f'    <resource identifier="{meta_dep_id}" type="associatedcontent/imscc_xmlv1p1/learning-application-resource" href="{assessment_id}/assessment_meta.xml">',
        f'      <file href="{assessment_id}/assessment_meta.xml"/>',
        '    </resource>',
        '  </resources>',
        '</manifest>'
    ]
    return "\n".join(xml)


def create_qti_zip(output_path):
    assessment_id = "quiz_01_assessment"
    assignment_id = "quiz_01_assignment"
    manifest_id = "quiz_01_manifest"
    meta_dep_id = "quiz_01_meta_dep"

    qti_xml = build_qti_xml(assessment_id, TOPICS)
    meta_xml = build_assessment_meta_xml(assessment_id, assignment_id, TOPICS)
    manifest_xml = build_manifest_xml(manifest_id, assessment_id, meta_dep_id)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("imsmanifest.xml", manifest_xml.encode("utf-8"))
        zf.writestr(f"{assessment_id}/{assessment_id}.xml", qti_xml.encode("utf-8"))
        zf.writestr(f"{assessment_id}/assessment_meta.xml", meta_xml.encode("utf-8"))

    print(f"Generated QTI zip: {output_path}")


if __name__ == "__main__":
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz_01_program_intro.zip")
    create_qti_zip(out_file)
