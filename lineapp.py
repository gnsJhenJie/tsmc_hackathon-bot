from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, PostbackEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageTemplateAction, PostbackAction
)
import os
import requests

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])

register_url = "https://tsmc.gnsjhenjie.tech/api/registerLine"
management_secret = os.environ['WEB_MANAGEMENT_SECRET']

@app.route("/sendIncident", methods=['POST'])
def sendIncident():
    print(request.form.get('line_user_id'))
    incident_id = request.form.get('incident_id')
    area = request.form.get('area')
    created_at = request.form.get('created_at')
    without_amount = request.form.get('without_amount')
    line_bot_api.push_message(request.form.get('line_user_id'), [
        TextSendMessage(text="未戴安全帽通報!"),
        TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                title='未戴安全帽違規通報(自動偵測)',
                text="#"+incident_id+"\n地點:"+area+"\n時間:"+created_at+"\n違規人數:"+without_amount+"人",
                # thumbnailImageUrl='https://tsmc.gnsjhenjie.tech/incident/image/30',
                actions=[
                    PostbackAction(
                        label='處理完成',
                        display_text='#'+incident_id+"已標記為完成",
                        data='_done_#'+incident_id
                    ),
                    PostbackAction(
                        label='標記為誤報',
                        text='#'+incident_id+"已標記為誤報",
                        data='_mis_#'+incident_id 
                    ),
                ]
            )
        )
    ])

    return "OK"

@app.route("/callback", methods=['POST']) ## 接 POST 需求
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature) ## 丟到 Handler 去處理訊息
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(event.source.user_id)
    if event.message.text.find("register:") == 0:
        payload={'management_secret': management_secret,
        'line_user_id': event.source.user_id,
        'register_token': event.message.text.replace("register:","")}
        response = requests.request("POST", register_url, data=payload)
        print(response.text)

        if response.text == "Success":
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Registered!"))
        else:
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Failed!"))
    elif event.message.text == "test1":
        line_bot_api.push_message(event.source.user_id, [
            TextSendMessage(text="未戴安全帽通報!"),
            TemplateSendMessage(
                alt_text='Buttons template',
                template=ButtonsTemplate(
                    title='未戴安全帽違規通報(自動偵測)',
                    text='地點:六廠A區-3F樓梯口\n時間:2022/12/15 13:03\n違規人數:5人',
                    thumbnailImageUrl='https://tsmc.gnsjhenjie.tech/incident/image/30',
                    actions=[
                        MessageTemplateAction(
                            label='處理完成',
                            text='六廠A區-3F樓梯口-處理完成',
                            payload="delete30"
                        ),
                        MessageTemplateAction(
                            label='標記為誤報',
                            text='六廠A區-3F樓梯口-標記為誤報',
                        ),
                    ]
                )
            )
        ])
    else:    
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)) ## 回傳 User 剛剛所傳的訊息 (Echo Bot)

@handler.add(PostbackEvent)
def handle_postback_event(event):
    print(event.postback.data)
    if event.postback.data.find('_done_#') != -1:
        payload={'management_secret': management_secret,'_method': "PUT"}
        response = requests.request("PUT", "https://tsmc.gnsjhenjie.tech/api/incident/"+event.postback.data.replace('_done_#',''))
        print(response.text)

        if response.text == "Success":
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Success!"))
        else:
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Failed!"))
    elif event.postback.data.find('_mis_#') != -1: 
        payload={'management_secret': management_secret,'_method': "DELETE"}
        print(event.postback.data.replace('_mis_#',''))
        response = requests.request("DELETE", "https://tsmc.gnsjhenjie.tech/api/incident/"+event.postback.data.replace('_mis_#',''))
        print(response.text)

        if response.text == "Success":
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Success!"))
        else:
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="Failed!"))
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3003)
