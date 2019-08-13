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
from . import pluginstore
from . import audioengine

import threading
import os
from naomi import profile


class WebUI(object):

    def __init__(self,  mic, conversation, in_out_device):
        self.mic = mic
        self.conversation = conversation
        global audio_devices
        audio_devices = in_out_device

        profile.get_profile()

        host = profile.get_profile_var(['webui', 'Host'], '127.0.0.1')

        port = profile.get_profile_var(['webui','Port'], 5000 )

        # create thread for http listener
        t = threading.Thread(target=self.startWebUI,
                             args=(host, port))
        t.daemon = True
        t.start()

    def startWebUI(self, host, port):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        dir_path = os.path.join(dir_path, 'data', 'templates')

        app = Flask(__name__, template_folder=dir_path)
        app.config['SECRET_KEY'] = 'hard to guess string'
        bootstrap = Bootstrap(app)

        def toTuple(engine):
            choices = []
            for e in engine:
                form = (e, e)
                choices.append(form)
            return choices

        @app.route('/')
        def home():
            name = profile.get_profile_var(['first_name'])
            return render_template('index.html',
                                    name = name )


        @app.route('/setup', methods=['GET', 'POST'])
        def setup():


            name = profile.get_profile_var(['first_name'])
            last_name = profile.get_profile_var(['last_name'])
            email = profile.get_profile_var(['email', 'address'])
            keyword = profile.get_profile_var(['keyword'])
            language = profile.get_profile_var(['language'])
            user_form = UserProfileForm(
                                        name = name,
                                        last_name = last_name,
                                        email = email,
                                        keyword = keyword,
                                        language=language
                                        )
            print(user_form.name)

            stt_form = []

            deepspeech_stt = DeepspeechSTT()
            witai_stt = WitaiSTT()
            #witai_stt.display()
            pocketsphinx_stt = PocketsphinxSTT()
            julius_stt = JuliusSTT()
            kaldi_stt = KaldiSTT()
            watson_stt = WatsonSTT()

            stt_form.append(deepspeech_stt)
            stt_form.append(witai_stt)
            stt_form.append(pocketsphinx_stt)
            stt_form.append(julius_stt)
            stt_form.append(kaldi_stt)
            stt_form.append(watson_stt)

            tts_form = []

            pico_tts = PicoTTS()
            mary_tts = MaryTTS()
            flite_tts = FliteTTS()
            espeak_tts = EspeakTTS()

            tts_form.append(pico_tts)
            tts_form.append(mary_tts)
            tts_form.append(flite_tts)
            tts_form.append(espeak_tts)


            audio_engine = profile.get_profile_var(['audio_engine'])
            Audio_input = profile.get_profile_var(['audio','input_device'])
            Audio_output = profile.get_profile_var(['audio','output_device'])
            audio_form = AudioProfileForm(Audio_engine = audio_engine,
                                          Audio_output = Audio_output,
                                          Audio_input = Audio_input
                                          )
            current_stt = profile.get_profile_var(['active_stt','engine'])

            current_tts = profile.get_profile_var(['tts_engine'])

            if user_form.validate_on_submit() and user_form.submit_user.data:
                profile.set_profile_var(['first_name'], user_form.name.data)
                profile.set_profile_var(['last_name'], user_form.last_name.data)
                profile.set_profile_var(['keyword'], user_form.keyword.data)
                profile.set_profile_var(['language'], user_form.language.data)
                profile.set_profile_var(['email', 'address'], user_form.email.data)
                
                profile.save_profile()
                flash('You have sucessfully changed your user profile', category='success')
                return redirect(url_for('setup'))

            elif witai_stt.validate_on_submit() and witai_stt.submit_witai.data:
                witai_stt.save()
                return redirect(url_for('setup'))

            elif deepspeech_stt.validate_on_submit() and deepspeech_stt.submit_deepspeech.data:
                deepspeech_stt.save()
                return redirect(url_for('setup'))

            elif pocketsphinx_stt.validate_on_submit() and pocketsphinx_stt.submit_pocketsphinx.data:
                pocketsphinx_stt.save()
                return redirect(url_for('setup'))

            elif julius_stt.validate_on_submit() and julius_stt.submit_julius.data:
                julius_stt.save()
                return redirect(url_for('setup'))

            elif kaldi_stt.validate_on_submit() and kaldi_stt.submit_kaldi.data:
                kaldi_stt.save()
                return redirect(url_for('setup'))

            elif watson_stt.validate_on_submit() and watson_stt.submit_watson.data:
                watson_stt.save()
                return redirect(url_for('setup'))

            elif pico_tts.validate_on_submit() and pico_tts.submit_pico.data:
                pico_tts.save()
                return redirect(url_for('setup'))

            elif mary_tts.validate_on_submit() and mary_tts.submit_mary.data:
                mary_tts.save()
                return redirect(url_for('setup'))

            elif audio_form.validate_on_submit() and audio_form.submit_audio.data:
                profile.set_profile_var(['audio_engine'], audio_form.Audio_engine.data)
                profile.set_profile_var(['audio', 'input_device'], audio_form.Audio_input.data)
                profile.set_profile_var(['audio', 'output_device'], audio_form.Audio_output.data)
                profile.save_profile()
                flash('You have sucessfully changed your Audio setup', category='success')
                return redirect(url_for('setup'))





            return render_template('form.html',
                                   user_form = user_form,
                                    stt_form = stt_form,
                                    tts_form = tts_form,
                                    audio_form = audio_form,
                                    current_stt = current_stt,
                                    current_tts = current_tts,
                                    name = name )

        @app.errorhandler(404)
        def page_not_found(e):
            return render_template('404.html'), 404

        @app.errorhandler(500)
        def internat_server_error(e):
            return render_template('500.html'), 500

        class UserProfileForm(FlaskForm):
            choices=[('en-US', 'English-US'), ('fr-FR', 'French-FR'),  ('de-DE', 'Deutch-DE')]
            name = StringField('Your name*' ,validators=[DataRequired()])
            last_name = StringField('Your last name')
            phone_number = StringField('Your phone number')
            email = StringField('Your email' ,validators=[Email()])
            keyword = StringField('Your personnal Keyword*', validators=[DataRequired()] )
            language = SelectField('Language*', choices=choices, validators=[DataRequired()])
            submit_user = SubmitField('Submit')

        class WitaiSTT(FlaskForm):
            name = "Wit.ai"
            profile_key = "witai-stt"

            stt_key = profile.get_profile_var(['witai-stt', 'access_token'], "")

            key = StringField('Your key', default=stt_key, validators=[DataRequired()] )
            submit_witai = SubmitField('Submit')

            def save(self):
                data = self.data
                profile.set_profile_var(['witai-stt', 'access_token'], data["key"])
                profile.save_profile()

        class DeepspeechSTT(FlaskForm):
            name = "DeepSpeech"
            profile_key = "deepspeech-stt"

            model_value = profile.get_profile_var(['deepspeech','model'])
            alphabet_value = profile.get_profile_var(['deepspeech','alphabet'])
            language_model_value = profile.get_profile_var(['deepspeech', 'language_model'])
            trie_value = profile.get_profile_var(['deepspeech', 'trie'])

            model = StringField('Path to your output_graph.pb file', default=model_value, validators=[DataRequired()] )
            alphabet = StringField('Path to your alphabet.txt file', default=alphabet_value, validators=[DataRequired()] )
            language_model = StringField('Path to your lm.binary file', default=language_model_value, validators=[DataRequired()] )
            trie = StringField('Path to your trie file', default=trie_value ,validators=[DataRequired()] )
            submit_deepspeech = SubmitField('Submit')

            def save(self):
                data = self.data
                profile.set_profile_var(['deepspeech', 'model'], data['model'])
                profile.set_profile_var(['deepspeech', 'alphabet'], data['alphabet'])
                profile.set_profile_var(['deepspeech', 'language_model'], data['language_model'])
                profile.set_profile_var(['deepspeech', 'trie'], data['trie'])
                profile.save_profile()

        class PocketsphinxSTT(FlaskForm):
            name = "PocketSphinx"
            profile_key = "sphinx"

            fst_model_value = profile.get_profile_var(['pocketsphinx', 'fst_model'])
            hmm_dir_value = profile.get_profile_var(['pocketsphinx', 'hmm_dir'])
            phonetisaurus_executable_value = profile.get_profile_var(['pocketsphinx', 'phonetisaurus_executable'], 'phonetisaurus-g2pfst')

            model = StringField('Your fst model path', default=fst_model_value, validators=[DataRequired()])
            hmm_dir = StringField('Your hmm directory path', default=hmm_dir_value, validators=[DataRequired()])
            executable = StringField('Your phonetisaurus executable file', default=phonetisaurus_executable_value, validators=[DataRequired()])

            submit_pocketsphinx = SubmitField('Submit')

            def save(self):
                data = self.data
                profile.set_profile_var(['pocketsphinx', 'fst_model'], data['model'])
                profile.set_profile_var(['pocketsphinx', 'hmm_dir'], data['hmm_dir'])
                profile.set_profile_var(['pocketsphinx', 'phonetisautus_executable'], data['executable'])
                profile.save_profile()

        class JuliusSTT(FlaskForm):
            name = "Julius"
            profile_key = "julius-stt"

            hmmdefs_value = profile.get_profile_var(['julius', 'hmmdefs'])
            tiedlist_value = profile.get_profile_var(['julius', 'tiedlist'])

            hmmdefs = StringField('Your hmmdefs vocabulary model file path', default=hmmdefs_value ,validators=[DataRequired()])
            tiedlist = StringField('Your tiedlist accoustic model file path', default=tiedlist_value, validators=[DataRequired()])

            submit_julius = SubmitField('Submit')

            def save(self):
                    data = self.data
                    profile.set_profile_var(['julius', 'hmmdefs'], data['hmmdefs'])
                    profile.set_profile_var(['julius', 'tiedlist'], data['tiedlist'])
                    profile.save_profile()

        class WatsonSTT(FlaskForm):
            name = "IBM Watson Speech To Text"
            profile_key = "watson"

            username_value = profile.get_profile_var(['watson_stt', 'username'])
            password_value = profile.get_profile_var(['watson_stt', 'password'])
            model_value = profile.get_profile_var(['watson_stt', 'model'], 'en-US_BroadbandModel')

            username = StringField('Your IBM account username', default=username_value, validators=[DataRequired()])

            password = StringField('Your IBM account password', default=password_value, validators=[DataRequired()])
            model = StringField('Your language model', default=model_value, validators=[DataRequired()])

            submit_watson = SubmitField('Submit')

            def save(self):
                data = self.data
                profile.set_profile_var(['watson_stt', 'username'], data['username'])
                profile.set_profile_var(['watson_stt', 'password'], data['password'])
                profile.set_profile_var(['watson_stt', 'model'], data['model'])
                profile.save_profile()

        class KaldiSTT(FlaskForm):
            name = "Kaldi"
            profile_key = "kaldigstserver-stt"

            url_value = profile.get_profile_var(['kaligstserver-stt', 'url'])
            url = StringField('Your kaldi server URL', default=url_value, validators=[DataRequired()])

            submit_kaldi = SubmitField('Submit')

            def save(self):
                data = self.data
                profile.set_profile_var(['kaldigstserver-stt', 'url'], data['url'] )
                profile.save_profile()

        class PicoTTS(FlaskForm):
            name = "SvoxPico"
            profile_key = "pico-tts"

            submit_pico = SubmitField('Submit')

            def save(self):
                profile.set_profile_var(['tts_engine'], 'pico-tts')
                profile.save_profile()

        class MaryTTS(FlaskForm):
            name = "MaryTTS"
            choices = choices=[('en-US', 'English-US'), ('fr-FR', 'French-FR'),  ('de-DE', 'Deutch-DE'), ('it-IT', 'Italian-IT'), ('tr-TR','Turkish-TK'), ('te-TE', 'Telugu-TE')]
            profile_key = "mary-tts"

            server_value = profile.get_profile_var(['mary-tts', 'server'])
            port_value = profile.get_profile_var(['mary-tts', 'port'])
            language_value = profile.get_profile_var(['mary-tts', 'language'], 'en_US')
            voice_value = profile.get_profile_var(['mary-tts', 'voicie'])

            server = StringField('MaryTTS server URL', default=server_value, validators=[DataRequired()])
            port = StringField('MaryTTS server Port', default=port_value, validators=[DataRequired()])
            language = SelectField('MaryTTS language', default=language_value, choices=choices, validators=[DataRequired()])
            voice = StringField('MaryTTS voice', default=voice_value, validators=[DataRequired()])


            submit_mary = SubmitField('Submit')

            def save(self):
                data = self.data

                profile.set_profile_var(['tts_engine'], 'mary-tts')
                profile.set_profile_var(['mary-tts', 'server'], data['server'])
                profile.set_profile_var(['mary-tts', 'port'], data['port'])
                profile.set_profile_var(['mary-tts', 'language'], data['language'])
                profile.set_profile_var(['mary-tts', 'language'], data['voice'])
                profile.save_profile()

        class FliteTTS(FlaskForm):
            name= "FliteTTS"

            voice_value = profile.get_profile_var(['flite-tts', 'voice'])

            voice = StringField('Flite Voice (optional, only for English)')
            submit_flite = SubmitField('Submit')

            def save(self):
                data = self.data
                profile.set_profile_var(['tts_engine'], 'flite-tts')
                if data['voice'] != '':
                    profile.set_profile_var(['flite-tts', 'voice'], data['voice'])
                profile.save_profile()

        class EspeakTTS(FlaskForm):
            name= "Espeak"

            voice_value = profile.get_profile_var(['espeak-tts', 'voice'])
            pitch_adjustment_value = profile.get_profile_var(['espeak-tts', 'pitch_adjustment'])
            words_pm_value = profile.get_profile_var(['espeak-tts', 'words_per_minute'])

            voice = StringField('Espeak Voice (Optional)', default=voice_value)
            pitch_adjustment = StringField('Espeak Pitch Adjustment (Optional)', default=pitch_adjustment_value)
            words_per_minute = StringField('Espeak debit (in words per minute) (Optional)', default=words_pm_value)

            def save(self):
                data = self.data
                profile.set_profile_var(['tts_engine'], 'espeak-tts')
                if data['voice'] != "" :
                    profile.set_profile_var(['espeak-tts', 'voice'], data['voice'])
                if data['pitch_adjustment'] != "":
                      profile.set_profile_var(['espeak-tts', 'pitch_adjustment'], data['pitch_adjustment'])
                if data['words_per_minute'] != "":
                      profile.set_profile_var(['espeak-tts', 'words_per_minute'], data['words_per_minute'])
                profile.save_profile()



        class AudioProfileForm(FlaskForm):
            engine_choices = [('alsa', 'Alsa'), ('pyaudio', 'PyAudio')]
            Audio_engine = SelectField('Engine', choices=engine_choices, validators=[DataRequired()])
            Audio_input = SelectField('Input', choices=toTuple(audio_devices["input"]), validators=[DataRequired()])
            Audio_output = SelectField('Output', choices=toTuple(audio_devices["output"]), validators=[DataRequired()])
            submit_audio = SubmitField('Submit')

        # start
        app.run(host=host, port=port, debug=False)
