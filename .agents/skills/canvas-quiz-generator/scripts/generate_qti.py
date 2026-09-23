#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas LMS QTI 1.2 Quiz Package Generator
任意の小テスト定義（JSONファイルまたは辞書）から、
Canvas LMSにインポート可能なQTI 1.2 zipパッケージを生成する汎用スクリプト。
"""

import argparse
import html
import json
import os
import sys
import zipfile


def build_qti_xml(assessment_id, title, topics, default_points=1.0):
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.imsglobal.org/xsd/ims_qtiasiv1p2 http://www.imsglobal.org/xsd/ims_qtiasiv1p2p1.xsd">',
        f'  <assessment ident="{assessment_id}" title="{html.escape(title)}">',
        '    <qtimetadata>',
        '      <qtimetadatafield>',
        '        <fieldlabel>cc_maxattempts</fieldlabel>',
        '        <fieldentry>1</fieldentry>',
        '      </qtimetadatafield>',
        '    </qtimetadata>',
        '    <section ident="root_section">'
    ]

    for topic in topics:
        group_id = topic.get("group_id", f"group_{len(xml)}")
        group_title = html.escape(topic.get("title", "問題グループ"))
        pick = topic.get("pick", 1)
        pts = topic.get("points_per_item", default_points)

        xml.append(f'      <section ident="{group_id}" title="{group_title}">')
        xml.append('        <selection_ordering>')
        xml.append('          <selection>')
        xml.append(f'            <selection_number>{pick}</selection_number>')
        xml.append('            <selection_extension>')
        xml.append(f'              <points_per_item>{pts:.1f}</points_per_item>')
        xml.append('            </selection_extension>')
        xml.append('          </selection>')
        xml.append('        </selection_ordering>')

        for q in topic.get("questions", []):
            qid = q.get("id", f"q_{len(xml)}")
            qtitle = html.escape(q.get("title", qid))
            prompt = q.get("prompt", "")
            ans_list = q.get("answers", [])
            explanation = q.get("explanation", "")

            ans_ids = [f"{qid}_ans_{i}" for i in range(len(ans_list))]
            correct_ans_id = None
            for idx, a in enumerate(ans_list):
                if isinstance(a, (list, tuple)):
                    is_corr = a[1]
                elif isinstance(a, dict):
                    is_corr = a.get("correct", False)
                else:
                    is_corr = False
                if is_corr:
                    correct_ans_id = ans_ids[idx]

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

            for a_id, a in zip(ans_ids, ans_list):
                if isinstance(a, (list, tuple)):
                    a_text = a[0]
                elif isinstance(a, dict):
                    a_text = a.get("text", "")
                else:
                    a_text = str(a)

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
            if correct_ans_id:
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


def build_assessment_meta_xml(assessment_id, assignment_id, title, description, topics, default_points=1.0):
    total_points = sum(t.get("pick", 1) * t.get("points_per_item", default_points) for t in topics)
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<quiz identifier="{assessment_id}" xmlns="http://canvas.instructure.com/xsd/cccv1p0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd">',
        f'  <title>{html.escape(title)}</title>',
        f'  <description>{html.escape(description)}</description>',
        '  <shuffle_answers>true</shuffle_answers>',
        '  <scoring_policy>keep_highest</scoring_policy>',
        '  <hide_results></hide_results>',
        '  <quiz_type>assignment</quiz_type>',
        f'  <points_possible>{total_points:.1f}</points_possible>',
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
        gid = topic.get("group_id", "")
        gtitle = html.escape(topic.get("title", ""))
        pick = topic.get("pick", 1)
        pts = topic.get("points_per_item", default_points)
        xml.append(f'    <quiz_group identifier="{gid}">')
        xml.append(f'      <title>{gtitle}</title>')
        xml.append(f'      <question_points>{pts:.1f}</question_points>')
        xml.append(f'      <pick_count>{pick}</pick_count>')
        xml.append('    </quiz_group>')

    xml.extend([
        '  </quiz_groups>',
        f'  <assignment_group_identifierref>assignment_group_{assessment_id}</assignment_group_identifierref>',
        f'  <assignment identifier="{assignment_id}">',
        f'    <title>{html.escape(title)}</title>',
        '    <due_at/>',
        '    <lock_at/>',
        '    <unlock_at/>',
        '    <module_locked>false</module_locked>',
        '    <workflow_state>published</workflow_state>',
        '    <assignment_overrides/>',
        f'    <quiz_identifierref>{assessment_id}</quiz_identifierref>',
        '    <allowed_extensions/>',
        '    <has_group_category>false</has_group_category>',
        f'    <points_possible>{total_points:.1f}</points_possible>',
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


def build_manifest_xml(manifest_id, assessment_id, meta_dep_id, title):
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<manifest identifier="{manifest_id}" xmlns="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1" xmlns:lom="http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource" xmlns:imsmd="http://www.imsglobal.org/xsd/imsmd_v1p2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1 http://www.imsglobal.org/xsd/imscp_v1p1.xsd http://ltsc.ieee.org/xsd/imsccv1p1/LOM/resource http://www.imsglobal.org/profile/cc/ccv1p1/LOM/ccv1p1_lomresource_v1p0.xsd http://www.imsglobal.org/xsd/imsmd_v1p2 http://www.imsglobal.org/xsd/imsmd_v1p2p2.xsd">',
        '  <metadata>',
        '    <schema>IMS Content</schema>',
        '    <schemaversion>1.1.3</schemaversion>',
        '    <imsmd:lom>',
        '      <imsmd:general>',
        '        <imsmd:title>',
        f'          <imsmd:string>{html.escape(title)}</imsmd:string>',
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


def generate_quiz_zip_from_data(data, output_path):
    quiz_id = data.get("quiz_id", "quiz_default")
    assessment_id = f"{quiz_id}_assessment"
    assignment_id = f"{quiz_id}_assignment"
    manifest_id = f"{quiz_id}_manifest"
    meta_dep_id = f"{quiz_id}_meta_dep"

    title = data.get("title", "小テスト")
    desc = data.get("description", "<p>理解度確認小テストです。</p>")
    topics = data.get("topics", [])
    default_points = data.get("points_per_item", 1.0)

    qti_xml = build_qti_xml(assessment_id, title, topics, default_points)
    meta_xml = build_assessment_meta_xml(assessment_id, assignment_id, title, desc, topics, default_points)
    manifest_xml = build_manifest_xml(manifest_id, assessment_id, meta_dep_id, title)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("imsmanifest.xml", manifest_xml.encode("utf-8"))
        zf.writestr(f"{assessment_id}/{assessment_id}.xml", qti_xml.encode("utf-8"))
        zf.writestr(f"{assessment_id}/assessment_meta.xml", meta_xml.encode("utf-8"))

    print(f"Successfully generated Canvas QTI package: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate Canvas LMS QTI 1.2 zip from JSON definition.")
    parser.add_argument("input_json", help="Path to input JSON file containing quiz definition.")
    parser.add_argument("-o", "--output", help="Path to output zip file (defaults to [quiz_id].zip in current directory).")
    args = parser.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    out_path = args.output
    if not out_path:
        qid = data.get("quiz_id", "quiz_package")
        out_path = f"{qid}.zip"

    generate_quiz_zip_from_data(data, out_path)


if __name__ == "__main__":
    main()
