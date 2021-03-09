import re,redis
from random import randint
import os

from flask import Flask,Blueprint,render_template,request,redirect,flash,url_for
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from flask_wtf import FlaskForm


from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from datetime import datetime

from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
# 导入 SMS 模块的client models
from tencentcloud.sms.v20190711 import sms_client, models
# 导入可选配置类
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile

app = Flask(__name__)

app.debug = True
app.secret_key = 'dev'

app.config['BOOTSTRAP_SERVE_FROM_LOCAL'] = True

bootstrap = Bootstrap(app)
csrf = CSRFProtect(app)

r = redis.Redis()



# 用于手机号验证的表单类
class PhoneVerificationForm(FlaskForm):
    phone = StringField('请输入手机号', validators=[DataRequired()])  # 手机号
    code = StringField('请输入验证码', validators=[DataRequired()])  # 验证码
    submit = SubmitField('验证')

    def validate_phone(form, field):  # 验证手机号格式
        if not _validate_phone(field.data):
            raise ValidationError('Invalid phone number')

# 用于邀请码验证的表单类
class VipcodeVerificationForm(FlaskForm):
  vipcode = StringField('邀请码',validators=[DataRequired()])
  submit = SubmitField('提交')

def _validate_phone(phone):
    if len(str(phone)) != 11:  # 验证长度
        return False
    if not re.match(r'1[3-9]\d{9}', phone):  # 验证格式
        return False
    return True

def send_sms(phone, code): 
    try:
        # 必要步骤：
        # 实例化一个认证对象，入参需要传入腾讯云账户密钥对 secretId 和 secretKey
        # 本示例采用从环境变量读取的方式，需要预先在环境变量中设置这两个值
        # 您也可以直接在代码中写入密钥对，但需谨防泄露，不要将代码复制、上传或者分享给他人
        # CAM 密钥查询：https://console.cloud.tencent.com/cam/capi

        cred = credential.Credential("AKIDwvpT0Mxj1MVaTAQS740vof1LbkuxfV0b", "YuMhCboskQyKUSErJfpwviMo4BQWQ8dv")
        # cred = credential.Credential(
        #     os.environ.get(""),
        #     os.environ.get("")
        # )
        # 实例化一个 http 选项，可选，无特殊需求时可以跳过
        httpProfile = HttpProfile()
        httpProfile.reqMethod = "POST"  # POST 请求（默认为 POST 请求）
        httpProfile.reqTimeout = 30    # 请求超时时间，单位为秒（默认60秒）
        httpProfile.endpoint = "sms.tencentcloudapi.com"  # 指定接入地域域名（默认就近接入）
        # 非必要步骤:
        # 实例化一个客户端配置对象，可以指定超时时间等配置
        clientProfile = ClientProfile()
        clientProfile.signMethod = "TC3-HMAC-SHA256"  # 指定签名算法
        clientProfile.language = "en-US"
        clientProfile.httpProfile = httpProfile
        # 实例化 SMS 的 client 对象
        # 第二个参数是地域信息，可以直接填写字符串 ap-guangzhou，或者引用预设的常量
        client = sms_client.SmsClient(cred, "ap-guangzhou", clientProfile)
        # 实例化一个请求对象，根据调用的接口和实际情况，可以进一步设置请求参数
        # 您可以直接查询 SDK 源码确定 SendSmsRequest 有哪些属性可以设置
        # 属性可能是基本类型，也可能引用了另一个数据结构
        # 推荐使用 IDE 进行开发，可以方便的跳转查阅各个接口和数据结构的文档说明
        req = models.SendSmsRequest()
        # 基本类型的设置:
        # SDK 采用的是指针风格指定参数，即使对于基本类型也需要用指针来对参数赋值
        # SDK 提供对基本类型的指针引用封装函数
        # 帮助链接：
        # 短信控制台：https://console.cloud.tencent.com/smsv2
        # sms helper：https://cloud.tencent.com/document/product/382/3773
        # 短信应用 ID: 在 [短信控制台] 添加应用后生成的实际 SDKAppID，例如1400006666
        req.SmsSdkAppid = "1400478575"
        # 短信签名内容: 使用 UTF-8 编码，必须填写已审核通过的签名，可登录 [短信控制台] 查看签名信息
        req.Sign = u'贞土CSA'
        # 短信码号扩展号: 默认未开通，如需开通请联系 [sms helper]
        req.ExtendCode = ""
        # 用户的 session 内容: 可以携带用户侧 ID 等上下文信息，server 会原样返回
        req.SessionContext = "xxx"
        # 国际/港澳台短信 senderid: 国内短信填空，默认未开通，如需开通请联系 [sms helper]
        req.SenderId = ""
        # 下发手机号码，采用 e.164 标准，+[国家或地区码][手机号]
        # 例如+8613711112222， 其中前面有一个+号 ，86为国家码，13711112222为手机号，最多不要超过200个手机号
        phone = '+86'+str(phone)
        req.PhoneNumberSet = [phone]
        # 模板 ID: 必须填写已审核通过的模板 ID，可登录 [短信控制台] 查看模板 ID
        req.TemplateID = "852435"
        # 模板参数: 若无模板参数，则设置为空
        req.TemplateParamSet = [code,"1"]
            # 通过 client 对象调用 SendSms 方法发起请求。注意请求方法名与请求对象是对应的
        resp = client.SendSms(req)
        # 输出 JSON 格式的字符串回包
        print(resp.to_json_string(indent=2))
    except TencentCloudSDKException as err:
        print(err)
    else:
        return True  

def get_value(phone, key):
    value = r.hget(phone, key)
    return value.decode('utf-8') if value else value

#手机、验证码，验证函数
def verify_code(phone, code):
    return get_value(phone, 'code') == code


#项目入口视图函数介绍：
    # 点击微信授权链接（携带微信code）而来的用户，通过code,获取微信用户身份信息，为该用户建立一条user表数据；
    # 渲染一个"阅读条款并同意"复选表单（内容：用户你好……用户告知……拿到邀请码的，请点击提交前往验证注册），如点击同意提交，则让该微信用户携带user表id重定向到以下视图函数。
    # 以下接收函数中，以变量userid = 1代替。

@app.route('/', methods=['GET', 'POST'])
def index(): 
    # from models import Vipcode #导入Vipcode模型类
  
    userid = 1

    form = VipcodeVerificationForm()

    if form.validate_on_submit():
        vipcode = form.vipcode.data
        # vipcode = Vipcode.query.filter_by(user_code=vipcode).first()
        # if vipcode and vipcode.status_code != 1: #如果该用户输入的邀请码有效，并且该邀请码的状态不是1，并且该用户已通过手机验证
        return redirect(url_for('bind',vipcode = vipcode,userid = userid)) #重定向记问bind页面时,携带此vipcode码

    return render_template('index.html', form=form)


@app.route('/bind/?<string:vipcode><string:userid>', methods=['GET', 'POST'])
def bind(vipcode,userid):
    
    print(vipcode,'---',userid) #test

    form = PhoneVerificationForm()
    if form.validate_on_submit():
        phone = form.phone.data
        code = form.code.data
        
        if not r.exists(phone):  
            flash('验证码错误或者过期', 'error')
            return redirect(url_for('bind',vipcode = vipcode,userid = userid))
        # 向user表存入手机号
        # 向user表存入验证码id
        # 向vipcode表status字段存入1
        # 对该用户执行登录（略）
        # 重定向去某个页面
        flash('手机验证通过！')
        # 在这里可以对用户数据库表示手机通过验证的字段进行更新
    return render_template('phonebind.html', form=form)
  

@app.route('/send-code', methods=['POST'])
def send_sms_code():
    phone = request.json.get('phone')  # 获取手机号
    # 验证手机号格式
    if not _validate_phone(phone):
        return {'message': '输入无效手机号'}, 400

    if r.exists(phone):
        created_time_str = get_value(phone, 'created_time')
        created_time = datetime.strptime(created_time_str, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        delta_seconds = (now - created_time).seconds
        if delta_seconds < 60:
            return {'message': '勿频繁操作'}, 400

    code = str(randint(100000, 999999))  # 生成随机验证码
    data = {
    'code': code,
    'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    r.hset(phone, mapping=data)
    r.expire(phone, 10 * 60)
    print(f'phone: {phone}, code: {code}')
    if send_sms(phone, code):  # 发送验证码短信，传入手机号和验证码
        return {'message': '验证码已发送！'}
    else:
        return {'message': 'Something was wrong'}, 500