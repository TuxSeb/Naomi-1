# -*- coding: utf-8 -*-
from flask import Flask, request, make_response, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import *
from flask_wtf.csrf import CSRFProtect
from flask_wtf.file import FileField
from wtforms.validators import DataRequired, Email
from werkzeug import secure_filename
from naomi import populate

import threading
import os
from naomi import profile

#from functools import wraps


class WebUI(object):

    def __init__(self,  mic, conversation):
        self.mic = mic
        self.conversation = conversation

        profile.get_profile()

        host = profile.get_profile_var(['webui', 'Host'], '127.0.0.1')

        port = profile.get_profile_var(['webui','Port'], 5000 )

        audio_engine = populate.get_audio_engines()

        # create thread for http listener
        t = threading.Thread(target=self.startWebUI,
                             args=(host, port))
        t.daemon = True
        t.start()

    def startWebUI(self, host, port):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        dir_path = os.path.join(dir_path, 'data', 'templates')

        #UPLOAD_FOLDER = '/home/seb/.naomi/configs/'
        app = Flask(__name__, template_folder=dir_path)
        app.config['SECRET_KEY'] = 'hard to guess string'
        bootstrap = Bootstrap(app)
        #app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

        @app.route('/', methods=['GET', 'POST'])
        def setup():



            name = profile.get_profile_var(['first_name'])
            last_name = profile.get_profile_var(['last_name'])
            email = profile.get_profile_var(['email'])
            keyword = profile.get_profile_var(['keyword'])
            language=profile.get_profile_var(['language'])
            user_form = UserProfileForm(
                                        name = name,
                                        last_name = last_name,
                                        email = email,
                                        keyword = keyword,
                                        language=language
                                        )

            stt_engine = profile.get_profile_var(['active_stt','engine'])
            stt_key = profile.get_profile_var(['key'])
            stt_form = STTProfileForm(
                                      STT_engine=stt_engine,
                                      STT_key = stt_key
                                      )

            tts_engine = profile.get_profile_var(['tts_engine'])
            tts_form = TTSProfileForm(TTS_engine=tts_engine)

            audio_engine = profile.get_profile_var(['audio_engine'])


            audio_form = AudioProfileForm(Audio_engine = audio_engine)

            file_form = ConfigFileForm()

            if user_form.validate_on_submit() and user_form.submit_user.data:
                profile.set_profile_var(['first_name'], user_form.name.data)
                profile.set_profile_var(['last_name'], user_form.last_name.data)
                profile.set_profile_var(['keyword'], user_form.keyword.data)
                profile.set_profile_var(['language'], user_form.language.data)
                profile.set_profile_var(['email'], user_form.email.data)
                #session['name'] = user_form.name.data
                flash('You have sucessfully changed your user profile')
                profile.save_profile()
                return redirect(url_for('setup'))

            elif stt_form.validate_on_submit() and stt_form.submit_STT.data:

                profile.set_profile_var(['active_stt','engine'], stt_form.STT_engine.data)
                profile.set_profile_var(['key'], stt_form.STT_key.data)
                profile.save_profile()
                flash('You have sucessfully changed your Speech To Text engine')
                return redirect(url_for('setup'))

            elif tts_form.validate_on_submit() and tts_form.submit_TTS.data:
                profile.set_profile_var(['tts_engine'], tts_form.TTS_engine.data)
                profile.set_profile_var([''], tts_form.TTS_key.data)
                profile.save_profile()
                flash('You have sucessfully changed your Text To Speech engine')
                return redirect(url_for('setup'))

            elif audio_form.validate_on_submit() and audio_form.submit_audio.data:
                profile.set_profile_var(['audio_engine'], audio_form.Audio_engine.data)
                print(audio_form)
                profile.save_profile()
                flash('You have sucessfully changed your Audio setup')
                return redirect(url_for('setup'))

            elif file_form.validate_on_submit() and file_form.submit_file.data:
                filename = secure_filename(file_form.file_config.data.filename)
                print(filename)
                file_form.file_config.data.save('upload/' + filename)
                flash('You have sucessfully uploaded your profile file')
                profile.save_profile()
                return redirect(url_for('setup'))




            return render_template('index.html',
                                   user_form = user_form,
                                    stt_form = stt_form,
                                    tts_form = tts_form,
                                    audio_form = audio_form,
                                    file_form = file_form,
                                    name = name )



        @app.route('/test', methods=['GET', 'POST'])
        def test():
            user_form = UserProfileForm()

            if user_form.validate_on_submit():

                old_name = profile.get_profile_var(['first_name'])
                if old_name is not None and old_name != user_form.name.data:
                    flash('Looks like you have changed your name!')
                    profile.set_profile_var(['first_name'], user_form.name.data)
                    name =  profile.get_profile_var(['first_name'])

                return redirect(url_for('test'))
            return render_template('index.html',
                                   user_form = user_form,
                                   name = profile.get_profile_var(['first_name']) )





        @app.errorhandler(404)
        def page_not_found(e):
            return render_template('404.html'), 404

        @app.errorhandler(500)
        def internat_server_error(e):
            return render_template('500.html'), 500

        def set_default_dropdown(path, choices):
            val = profile.get_profile_var(path)
            for i in choices:
                if(val == i[0]):
                    return i[0]
            return choices[0][0]

        class UserProfileForm(FlaskForm):
            choices=[('en-US', 'English-US'), ('fr-FR', 'French-FR'),  ('de-DE', 'Deutch-DE')]
            name = StringField('Your name' ,validators=[DataRequired()])
            last_name = StringField('Your last name', validators=[DataRequired()])
            email = StringField('Your email' ,validators=[Email()])
            keyword = StringField('Your personnal Keyword', validators=[DataRequired()] )
            language = SelectField('Language', choices=choices)
            submit_user = SubmitField('Submit')

        class STTProfileForm(FlaskForm):
            choices= [('pocketsphinx-stt', 'Pocketsphinx'), ('witai-stt','wit.AI'),
                        ('deepspeech-stt', 'DeepSpeech'), ('julius-stt', 'Julius'),
                        ('kaldigstserver-stt', 'Kaldi')]

            STT_engine = SelectField('Engine', choices=choices, validators=[DataRequired()])
            STT_key = StringField('Key or filepath', validators=[DataRequired()])
            submit_STT = SubmitField('Submit')



        class TTSProfileForm(FlaskForm):
            choices = [('festival-tts', 'Festival') , ('espeak-tts', 'Espeak'),
                       ('pico-tts', 'SvoxPico'), ('flite-tts', 'Flite'),
                       ('mary-tts', 'MaryTTS'), ('osx-tts', 'Say OSX'),
                       ('cereproc-tts', 'Cereproc'),
                       ('google-tts', 'Google TTS')]

            TTS_engine = SelectField('Engine', choices=choices, validators=[DataRequired()])
            TTS_key = StringField('Key or filepath')
            submit_TTS = SubmitField('Submit')

        class AudioProfileForm(FlaskForm):
            engine_choices = [('alsa', 'Alsa'), ('pyaudio', 'PyAudio')]

            Audio_engine = SelectField('Engine', choices=engine_choices, validators=[DataRequired()])
            #Audio_input = SelectField('Input', validators=[DataRequired()])
            #Audio_Output = SelectField('Output', validators=[DataRequired()])
            submit_audio = SubmitField('Submit')

        class ConfigFileForm(FlaskForm):
            file_config = FileField('Submit your profile file here ', validators=[DataRequired()])
            submit_file = SubmitField('Submit')







        # start
        app.run(host=host, port=port, debug=False)
