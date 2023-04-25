import tkinter
import pandas as pd
from redcap import Project
from tkinter import *
from tkinter import ttk
from pandastable import Table
from tkinter import messagebox
from redcap import request
from settings import user_info_t1d, user_info_survey
import warnings

warnings.filterwarnings('ignore', message="^Columns.*")

# REDCap api url
API_URL = 'https://redcap.ctsi.ufl.edu/redcap/api/'

# main window
login_window = Tk()
login_window.geometry('1200x900')
login_window.title('SNACMEATS Portal')

# title label
lbl_greeting = Label(login_window, text='Welcome to the SNACMEATS Portal!')
lbl_greeting.grid(row=0, column=1, sticky='nsew')

# frame to house username entry
frame_user_info = Frame(login_window, bd=5, relief='sunken')
frame_user_info.grid(row=1, column=1)

# label and entry box for username
lbl_username = Label(frame_user_info, text='Enter your GatorLink Username: ', font=('Arial', 10))
lbl_username.grid(row=1, column=0, pady=15)
entry_uname = Entry(frame_user_info, font=('Arial', 10))
entry_uname.grid(row=1, column=1, pady=15)


def on_double_click(event):
    # get selected item from tree view
    item_id = event.widget.focus()
    item = event.widget.item(item_id)
    values = item['values']

    # create new window
    analysis = tkinter.Toplevel()
    analysis.title('Request Analysis')

    # pull REDCap sample/data request report
    api_key_uname = entry_uname.get()
    api_key_data = user_info_t1d[api_key_uname]
    data = Project(API_URL, api_key_data)
    df = data.export_reports(format='df', report_id='34409', raw_or_label='label')

    # move donation id from index to a column and place it in the front
    df['donation_id_pk'] = df.index
    df = df[['donation_id_pk'] + [col for col in df.columns if col != 'donation_id_pk']]
    df[['donation_id_pk', 'aab_num_pos', 'dna_count', 'fresh_pbmc_count', 'heparin_count',
        'paxgene_count', 'plasma_e_count', 'serum_count', 'rested_pbmc_count', 'tempus_count']] = \
        df[['donation_id_pk', 'aab_num_pos', 'dna_count', 'fresh_pbmc_count', 'heparin_count',
            'paxgene_count', 'plasma_e_count', 'serum_count', 'rested_pbmc_count', 'tempus_count']].astype('Int64')
    df[['dna_count', 'fresh_pbmc_count', 'heparin_count', 'paxgene_count', 'plasma_e_count', 'serum_count',
        'rested_pbmc_count', 'tempus_count']] = \
        df[['dna_count', 'fresh_pbmc_count', 'heparin_count', 'paxgene_count', 'plasma_e_count', 'serum_count',
            'rested_pbmc_count', 'tempus_count']].fillna(0)
    df = df.loc[
        (df['project'] == 'P01') |
        (df['cohort'] == 'T1DExchange')]

    # is sample request
    if values[0] == 'Samples':
        # types of aliquots requested
        # 1 if it's a non-zero number, 0 otherwise; if not a number, something was entered, consider requested
        try:
            serum_requested = 1 if int(float(values[3])) != 0 else 0
        except:
            serum_requested = 1
        try:
            plasma_requested = 1 if int(float(values[4])) != 0 else 0
        except:
            plasma_requested = 1
        try:
            pbmc_requested = 1 if int(float(values[5])) != 0 else 0
        except:
            pbmc_requested = 1
        try:
            dna_requested = 1 if int(float(values[6])) != 0 else 0
        except:
            dna_requested = 1
        try:
            paxgene_requested = 1 if int(float(values[7])) != 0 else 0
        except:
            paxgene_requested = 1

        # types of clinical status requested
        # True if non-zero number or text entered, False otherwise
        try:
            controls_requested = True if int(float(values[8])) != 0 else False
        except:
            controls_requested = True
        try:
            relatives_requested = True if int(float(values[9])) != 0 else False
        except:
            relatives_requested = True
        try:
            aab_pos_relatives_requested = True if int(float(values[10])) != 0 else False
        except:
            aab_pos_relatives_requested = True
        try:
            new_onsets_requested = True if int(float(values[11])) != 0 else False
        except:
            new_onsets_requested = True
        try:
            t1d_requested = True if int(float(values[12])) != 0 else False
        except:
            t1d_requested = True
        try:
            t2d_requested = True if int(float(values[13])) != 0 else False
        except:
            t2d_requested = True

        # yes/no value for age/sex/hla match
        age_matched = values[14]
        sex_matched = values[16]
        hla_matched = values[20]

        # other parameters entered; not searched by, only to display
        age_range = values[15]
        sex_distribution = values[17]
        race_requirements = values[18]
        ethnicity_requirements = values[19]
        genotype_requested = values[21]

        # aliquot availability
        df = df.loc[
            (df['serum_count'] >= serum_requested) &
            (df['plasma_e_count'] >= plasma_requested) &
            ((df['fresh_pbmc_count'] >= pbmc_requested) | (df['rested_pbmc_count'] >= pbmc_requested)) &
            (df['dna_count'] >= dna_requested) &
            (df['paxgene_count'] >= paxgene_requested)]

        # clinical status availability
        statuses_requested = []
        if controls_requested:
            statuses_requested.append('Control')
        if relatives_requested:
            statuses_requested.append('First Degree Relative')
        if aab_pos_relatives_requested:
            statuses_requested.append('First Degree Relative')
        if new_onsets_requested:
            statuses_requested.append('New Onset')
        if t1d_requested:
            statuses_requested.append('T1D')
        if t2d_requested:
            statuses_requested.append('Type 2 Diabetes')
        df = df.loc[df['clinical_status'].isin(statuses_requested)]

        # if only aab-negative relatives requested
        if relatives_requested and not aab_pos_relatives_requested:
            df.drop(
                df[
                    (df['clinical_status'] == 'First Degree Relative') &
                    (df['aab_num_pos'].fillna(1) != 0)].index,
                inplace=True)

        # if only aab-positive relatives requested
        if aab_pos_relatives_requested and not relatives_requested:
            df.drop(
                df[
                    (df['clinical_status'] == 'First Degree Relative') &
                    (df['aab_num_pos'].fillna(0) == 0)].index,
                inplace=True)

        # only aab-negative controls valid
        if controls_requested:
            df.drop(
                df[
                    (df['clinical_status'] == 'Control') &
                    (df['aab_num_pos'] != 0)].index,
                inplace=True)

        # no duplicate donors, drop all instances after first
        df.drop_duplicates(subset='donor_id_pk', keep='first', inplace=True)

        # round age; sufficient in most cases, otherwise may need to floor/ceiling master list
        df['age'] = df['age'].fillna(0.0).round().astype(float).astype(int)

        # age/sex/hla match, add to list for function call
        params_to_match = []
        if age_matched == 'Yes':
            params_to_match.append('age')
        if sex_matched == 'Yes':
            params_to_match.append('gender')
        if hla_matched == 'Yes':
            params_to_match.append('hla')
            df = df[df['hla'].notnull()]

        # call function based on number of parameters to match
        # return empty dataframe if error thrown by function -> no results to display
        if len(params_to_match) == 3:
            try:
                df = triple_match(df)
            except:
                df = pd.DataFrame()
        elif len(params_to_match) == 2:
            try:
                df = double_match(df, params_to_match)
            except:
                df = pd.DataFrame()
        elif len(params_to_match) == 1:
            try:
                df = single_match(df, params_to_match)
            except:
                df = pd.DataFrame()

        my_font = ('Arial', 10)
        fr_table = Frame(analysis, bg='#ffffff', bd=5, relief='ridge')
        fr_table.grid(row=2, column=2)
        lbl_table = Label(fr_table, text='Diabase Output')
        lbl_table.pack()

        frame_table = Frame(analysis)
        frame_table.grid(row=3, column=2)

        table = Table(frame_table, dataframe=df, showstatusbar=True, editable=False, height=600, width=900)
        table.show()
        table.adjustColumnWidths()
        table.redraw()

        btn_export = Button(frame_table, text='Export Table', font=my_font, command=table.doExport)
        btn_export.grid(row=3, column=2, sticky='se')

        frame_summary = Frame(analysis)
        frame_summary.grid(row=3, column=5, padx=20)

        lbl_fr_displayed_summary = LabelFrame(frame_summary, text='Search Parameters', bd=5, relief='ridge')
        lbl_fr_displayed_summary.grid(row=2, column=5, padx=15, pady=50)

        # serum requested
        check_serum_requested = Checkbutton(lbl_fr_displayed_summary, text='Serum Requested', font=my_font)
        check_serum_requested.grid(row=2, column=2, sticky='w')
        check_serum_requested.deselect()
        if serum_requested > 0:
            check_serum_requested.select()
        check_serum_requested.config(state='disabled')

        # plasma requested
        check_plasma_requested = Checkbutton(lbl_fr_displayed_summary, text='Plasma Requested', font=my_font)
        check_plasma_requested.grid(row=3, column=2, sticky='w')
        check_plasma_requested.deselect()
        if plasma_requested > 0:
            check_plasma_requested.select()
        check_plasma_requested.config(state='disabled')

        # pbmc requested
        check_pbmc_requested = Checkbutton(lbl_fr_displayed_summary, text='PBMC Requested', font=my_font)
        check_pbmc_requested.grid(row=4, column=2, sticky='w')
        check_pbmc_requested.deselect()
        if pbmc_requested > 0:
            check_pbmc_requested.select()
        check_pbmc_requested.config(state='disabled')

        # dna requested
        check_dna_requested = Checkbutton(lbl_fr_displayed_summary, text='DNA Requested', font=my_font)
        check_dna_requested.grid(row=5, column=2, sticky='w')
        check_dna_requested.deselect()
        if dna_requested > 0:
            check_dna_requested.select()
        check_dna_requested.config(state='disabled')

        # paxgene requested
        check_paxgene_requested = Checkbutton(lbl_fr_displayed_summary, text='PAXGene Requested', font=my_font)
        check_paxgene_requested.grid(row=6, column=2, sticky='w')
        check_paxgene_requested.deselect()
        if paxgene_requested > 0:
            check_paxgene_requested.select()
        check_paxgene_requested.config(state='disabled')

        # age match results
        check_age_matched = Checkbutton(lbl_fr_displayed_summary, text='Age Matched', font=my_font)
        check_age_matched.grid(row=3, column=4, padx=25, sticky='w')
        check_age_matched.deselect()
        if age_matched == 'Yes':
            check_age_matched.select()
        check_age_matched.config(state='disabled')

        # sex match results
        check_sex_matched = Checkbutton(lbl_fr_displayed_summary, text='Sex Matched', font=my_font)
        check_sex_matched.grid(row=4, column=4, padx=25, sticky='w')
        check_sex_matched.deselect()
        if sex_matched == 'Yes':
            check_sex_matched.select()
        check_sex_matched.config(state='disabled')

        # hla match results
        check_hla_matched = Checkbutton(lbl_fr_displayed_summary, text='HLA Matched', font=my_font)
        check_hla_matched.grid(row=5, column=4, padx=25, sticky='w')
        check_hla_matched.deselect()
        if hla_matched == 'Yes':
            check_hla_matched.select()
        check_hla_matched.config(state='disabled')

        # additional (unchecked) parameters
        lbl_fr_additional_requests = LabelFrame(analysis, text='Additional Parameters (MANUALLY CHECK)', bd=5,
                                                relief='ridge')
        lbl_fr_additional_requests.grid(row=4, column=2, columnspan=10, padx=15, pady=15, sticky='w')

        # age range
        lbl_desired_age = Label(lbl_fr_additional_requests, text='Requested Age Range: ', font=my_font)
        lbl_desired_age.grid(row=0, column=1, padx=5, sticky='e')
        txt_desired_age = Text(lbl_fr_additional_requests, font=my_font, height=1, width=200)
        if len(str(age_range)) < 4:
            txt_desired_age.insert(INSERT, 'N/A')
        else:
            txt_desired_age.insert(INSERT, str(age_range))
        txt_desired_age.config(state='disabled')
        txt_desired_age.grid(row=0, column=2, pady=5, padx=5)

        # sex distribution
        lbl_desired_sex = Label(lbl_fr_additional_requests, text='Male/Female Distribution: ', font=my_font)
        lbl_desired_sex.grid(row=1, column=1, padx=5, sticky='e')
        txt_desired_sex = Text(lbl_fr_additional_requests, font=my_font, height=1, width=200)
        if len(str(sex_distribution)) < 4:
            txt_desired_sex.insert(INSERT, 'N/A')
        else:
            txt_desired_sex.insert(INSERT, str(sex_distribution))
        txt_desired_sex.config(state='disabled')
        txt_desired_sex.grid(row=1, column=2, pady=5, padx=5)

        # race requirements
        lbl_desired_race = Label(lbl_fr_additional_requests, text='Race Requirements: ', font=my_font)
        lbl_desired_race.grid(row=2, column=1, padx=5, sticky='e')
        txt_desired_race = Text(lbl_fr_additional_requests, font=my_font, height=1, width=200)
        if len(str(race_requirements)) < 4:
            txt_desired_race.insert(INSERT, 'N/A')
        else:
            txt_desired_race.insert(INSERT, str(race_requirements))
        txt_desired_race.config(state='disabled')
        txt_desired_race.grid(row=2, column=2, pady=5, padx=5)

        # ethnicity requirements
        lbl_desired_eth = Label(lbl_fr_additional_requests, text='Ethnicity Requirements: ', font=my_font)
        lbl_desired_eth.grid(row=3, column=1, padx=5, sticky='e')
        txt_desired_eth = Text(lbl_fr_additional_requests, font=my_font, height=1, width=200)
        if len(str(ethnicity_requirements)) < 4:
            txt_desired_eth.insert(INSERT, 'N/A')
        else:
            txt_desired_eth.insert(INSERT, str(ethnicity_requirements))
        txt_desired_eth.config(state='disabled')
        txt_desired_eth.grid(row=3, column=2, pady=5, padx=5)

        # genotype requested
        lbl_desired_genotype = Label(lbl_fr_additional_requests, text='Genotype Requirements: ', font=my_font)
        lbl_desired_genotype.grid(row=4, column=1, padx=5, sticky='e')
        txt_desired_genotype = Text(lbl_fr_additional_requests, font=my_font, height=1, width=200)
        if len(str(genotype_requested)) < 4:
            txt_desired_genotype.insert(INSERT, 'N/A')
        else:
            txt_desired_genotype.insert(INSERT, str(genotype_requested))
        txt_desired_genotype.config(state='disabled')
        txt_desired_genotype.grid(row=4, column=2, pady=5, padx=5)

        # displayed results
        lbl_fr_results_summary = LabelFrame(frame_summary, text='Summary of Results', bd=5, relief='ridge')
        lbl_fr_results_summary.grid(row=3, column=5, padx=15)

        # controls requested/displayed
        lbl_controls = Label(lbl_fr_results_summary, text='Controls Found: ', font=my_font)
        lbl_controls.grid(row=0, column=2, padx=10, sticky='e')
        entry_controls = Entry(lbl_fr_results_summary, width=5, font=my_font)
        try:
            entry_controls.insert(0, str(len(df[df['clinical_status'] == 'Control'])))
        except:
            entry_controls.insert(0, str(0))
        finally:
            entry_controls.config(state='disabled')
            entry_controls.grid(row=0, column=3, pady=5)

        lbl_controls_requested = Label(lbl_fr_results_summary, text='Controls Requested: ', font=my_font)
        lbl_controls_requested.grid(row=0, column=4, padx=10, sticky='e')
        entry_controls_requested = Entry(lbl_fr_results_summary, width=5, font=my_font)
        try:
            entry_controls_requested.insert(0, str(values[8]))
        except:
            entry_controls.insert(0, str(0))
        finally:
            entry_controls_requested.config(state='disabled')
            entry_controls_requested.grid(row=0, column=5, pady=5)

        # aab- relatives requested/displayed
        lbl_aab_neg_relatives = Label(lbl_fr_results_summary, text='AAb- Relatives Found: ', font=my_font)
        lbl_aab_neg_relatives.grid(row=1, column=2, padx=10)
        entry_aab_neg_relatives = Entry(lbl_fr_results_summary, width=5, font=my_font)
        try:
            entry_aab_neg_relatives.insert(0, str(len(
                df[(df['clinical_status'] == 'First Degree Relative') & (df['aab_num_pos'] == 0)])))
        except:
            entry_aab_neg_relatives.insert(0, str(0))
        finally:
            entry_aab_neg_relatives.config(state='disabled')
            entry_aab_neg_relatives.grid(row=1, column=3, pady=5, sticky='e')

        lbl_aab_neg_relatives_requested = Label(lbl_fr_results_summary, text='AAb- Relatives Requested: ', font=my_font)
        lbl_aab_neg_relatives_requested.grid(row=1, column=4, padx=10)
        entry_aab_neg_relatives_requested = Entry(lbl_fr_results_summary, width=5, font=my_font)
        try:
            entry_aab_neg_relatives_requested.insert(0, str(values[9]))
        except:
            entry_aab_neg_relatives_requested.insert(0, str(0))
        finally:
            entry_aab_neg_relatives_requested.config(state='disabled')
            entry_aab_neg_relatives_requested.grid(row=1, column=5, pady=5)

        # aab+ relatives requested/displayed
        lbl_aab_pos_relatives = Label(lbl_fr_results_summary, text='AAb+ Relatives Found: ', font=my_font)
        lbl_aab_pos_relatives.grid(row=2, column=2, padx=10, sticky='e')
        entry_aab_pos_relatives = Entry(lbl_fr_results_summary, width=5, font=my_font)
        try:
            entry_aab_pos_relatives.insert(0, str(len(
                df[(df['clinical_status'] == 'First Degree Relative') & (df['aab_num_pos'] > 0)])))
        except:
            entry_aab_pos_relatives.insert(0, str(0))
        finally:
            entry_aab_pos_relatives.config(state='disabled')
            entry_aab_pos_relatives.grid(row=2, column=3, pady=5)

        lbl_aab_pos_relatives_requested = Label(lbl_fr_results_summary, text='AAb+ Relatives Requested: ', font=my_font)
        lbl_aab_pos_relatives_requested.grid(row=2, column=4, padx=10, sticky='e')
        entry_aab_pos_relatives_requested = Entry(lbl_fr_results_summary, width=5, font=my_font)
        try:
            entry_aab_pos_relatives_requested.insert(0, str(values[10]))
        except:
            entry_aab_pos_relatives_requested.insert(0, str(0))
        finally:
            entry_aab_pos_relatives_requested.config(state='disabled')
            entry_aab_pos_relatives_requested.grid(row=2, column=5, pady=5)

        # new onsets requested/displayed
        lbl_new_onset = Label(lbl_fr_results_summary, text='New Onsets Found: ', font=my_font)
        lbl_new_onset.grid(row=3, column=2, padx=10, sticky='e')
        entry_new_onset = Entry(lbl_fr_results_summary, width=5, font=my_font)
        try:
            entry_new_onset.insert(0, str(len(df[df['clinical_status'] == 'New Onset'])))
        except:
            entry_new_onset.insert(0, str(0))
        finally:
            entry_new_onset.config(state='disabled')
            entry_new_onset.grid(row=3, column=3, pady=5)

        lbl_new_onset_requested = Label(lbl_fr_results_summary, text='New Onsets Requested: ', font=my_font)
        lbl_new_onset_requested.grid(row=3, column=4, padx=10, sticky='e')
        entry_new_onset_requested = Entry(lbl_fr_results_summary, width=5, font=my_font)
        try:
            entry_new_onset_requested.insert(0, str(values[11]))
        except:
            entry_new_onset_requested.insert(0, str(0))
        finally:
            entry_new_onset_requested.config(state='disabled')
            entry_new_onset_requested.grid(row=3, column=5, pady=5)

        # t1d requested/displayed
        lbl_t1d = Label(lbl_fr_results_summary, text='T1D Found: ', font=my_font)
        lbl_t1d.grid(row=4, column=2, padx=10, sticky='e')
        entry_t1d = Entry(lbl_fr_results_summary, width=5, font=my_font)
        try:
            entry_t1d.insert(0, str(len(df[df['clinical_status'] == 'T1D'])))
        except:
            entry_t1d.insert(0, str(0))
        finally:
            entry_t1d.config(state='disabled')
            entry_t1d.grid(row=4, column=3, pady=5)

        lbl_t1d_requested = Label(lbl_fr_results_summary, text='T1D Requested: ', font=my_font)
        lbl_t1d_requested.grid(row=4, column=4, padx=10, sticky='e')
        entry_t1d_requested = Entry(lbl_fr_results_summary, width=5, font=my_font)
        try:
            entry_t1d_requested.insert(0, str(values[12]))
        except:
            entry_t1d_requested.insert(0, str(0))
        finally:
            entry_t1d_requested.config(state='disabled')
            entry_t1d_requested.grid(row=4, column=5, pady=5)

        # t2d requested/displayed
        lbl_t2d = Label(lbl_fr_results_summary, text='T2D Found: ', font=my_font)
        lbl_t2d.grid(row=5, column=2, padx=10, sticky='e')
        entry_t2d = Entry(lbl_fr_results_summary, width=5, font=my_font)
        try:
            entry_t2d.insert(0, str(len(df[df['clinical_status'] == 'Type 2 Diabetes'])))
        except:
            entry_t2d.insert(0, str(0))
        finally:
            entry_t2d.config(state='disabled')
            entry_t2d.grid(row=5, column=3, pady=5)

        lbl_t2d_requested = Label(lbl_fr_results_summary, text='T1D Requested: ', font=my_font)
        lbl_t2d_requested.grid(row=5, column=4, padx=10, sticky='e')
        entry_t2d_requested = Entry(lbl_fr_results_summary, width=5, font=my_font)
        try:
            entry_t2d_requested.insert(0, str(values[13]))
        except:
            entry_t2d_requested.insert(0, str(0))
        finally:
            entry_t2d_requested.config(state='disabled')
            entry_t2d_requested.grid(row=5, column=5, pady=5)

    # is data request
    else:
        hla_yes_no = values[4]
        if hla_yes_no == 'Yes':
            df = df.loc[df['hla'].notnull()]

        lbl_fr_table = Frame(analysis, bg='#ffffff', bd=5, relief='ridge')
        lbl_fr_table.grid(row=2, column=2)
        lbl_table = Label(lbl_fr_table, text='Diabase Output')
        lbl_table.pack()

        frame_table = Frame(analysis)
        frame_table.grid(row=3, column=2)
        table = Table(frame_table, dataframe=df, showstatusbar=True, editable=False, height=600, width=550)
        table.show()


def login():
    api_key_uname = entry_uname.get()
    try:
        # take username from input and search for key
        api_key_survey = user_info_survey[api_key_uname]
        survey_export = Project(API_URL, api_key_survey)

        # use for sample requests
        sample_request_response = survey_export.export_records(format='df', raw_or_label='label')
        sample_request_response = sample_request_response.loc[
            sample_request_response['samples_or_data'] == 'Samples']
        sample_request_response = \
            sample_request_response[['samples_or_data', 'name_person', 'institution_name', 'serum_requested',
                                     'plasma_requested', 'pbmc_requested', 'dna_requested', 'paxgene_requested',
                                     'control_requested', 'relative_count', 'relative_aab_count', 'new_onset_count',
                                     't1d_count', 't2d_count', 'age_matched', 'requested_age_range', 'sex_matched',
                                     'sex_distribution', 'race_requirements', 'ethnicity_requirements',
                                     'genotype_hla_matched', 'genotype_requested']]
        sample_request_response['institution_name'] = \
            sample_request_response['institution_name'].fillna('University of Florida')
        sample_request_response = sample_request_response.fillna(0)

        sample_request_response[['control_requested', 'relative_count', 'relative_aab_count',
                                 'new_onset_count', 't1d_count', 't2d_count']] = \
            sample_request_response[['control_requested', 'relative_count', 'relative_aab_count',
                                     'new_onset_count', 't1d_count', 't2d_count']].astype('Int64')

        # use for data requests
        data_request_response = survey_export.export_records(format='df', raw_or_label='label')
        data_request_response = data_request_response.loc[data_request_response['samples_or_data'] == 'Data']
        data_request_response = data_request_response[['samples_or_data', 'name_person',
                                                       'institution_name', 'data_type',
                                                       'data_genome_assembly', 'data_snps', 'data_type_other',
                                                       'data_specific_subjects']]
        data_request_response['institution_name'] = \
            data_request_response['institution_name'].fillna('University of Florida')
        data_request_response = data_request_response.fillna(0)

        # create sample/data request tabs
        tab_samples_and_data = ttk.Notebook(login_window)
        frame_sample_request = Frame(tab_samples_and_data, height=600, width=1000)
        frame_sample_request.pack(fill='both', expand=True)
        frame_sample_request.pack_propagate(False)
        frame_data_request = Frame(tab_samples_and_data, height=600, width=1000)
        frame_data_request.pack(fill='both', expand=True)
        frame_data_request.pack_propagate(False)

        # create tree view for sample requests
        tree_samples = ttk.Treeview(frame_sample_request)
        tree_samples.place(relheight=1, relwidth=1)

        # add scrollbars for tree view: sample requests
        tree_samples_scroll_y = tkinter.Scrollbar(frame_sample_request, orient="vertical", command=tree_samples.yview)
        tree_samples_scroll_x = tkinter.Scrollbar(frame_sample_request, orient="horizontal",
                                                  command=tree_samples.xview)
        tree_samples.configure(xscrollcommand=tree_samples_scroll_x.set, yscrollcommand=tree_samples_scroll_y.set)
        tree_samples_scroll_x.pack(side="bottom", fill="x")
        tree_samples_scroll_y.pack(side="right", fill="y")

        # add columns to tree view: sample requests
        tree_samples['columns'] = list(sample_request_response.columns)
        tree_samples['show'] = 'headings'
        for column in tree_samples['columns']:
            tree_samples.heading(column, text=column)
            tree_samples.column(column, anchor='center')

        # add rows to tree view: samples requests
        sample_rows = sample_request_response.to_numpy().tolist()
        for row in sample_rows:
            tree_samples.insert("", 'end', values=row)

        # create tree view for data requests
        tree_data = ttk.Treeview(frame_data_request)
        tree_data.place(relheight=1, relwidth=1)

        # add scrollbars for tree view: data requests
        tree_data_scroll_y = tkinter.Scrollbar(frame_data_request, orient="vertical", command=tree_data.yview)
        tree_data_scroll_x = tkinter.Scrollbar(frame_data_request, orient="horizontal", command=tree_data.xview)
        tree_data.configure(xscrollcommand=tree_data_scroll_x.set, yscrollcommand=tree_data_scroll_y.set)
        tree_data_scroll_x.pack(side="bottom", fill="x")
        tree_data_scroll_y.pack(side="right", fill="y")

        # add columns to tree view: data requests
        tree_data['columns'] = list(data_request_response.columns)
        tree_data['show'] = 'headings'
        for column in tree_data['columns']:
            tree_data.heading(column, text=column)
            tree_data.column(column, anchor='center')

        # add rows to tree view: data requests
        data_rows = data_request_response.to_numpy().tolist()
        for row in data_rows:
            tree_data.insert("", 'end', values=row)

        # bind double click event to tree views
        tree_data.bind('<Double-Button-1>', on_double_click)
        tree_samples.bind('<Double-Button-1>', on_double_click)

        # add tree-views to respective tabs
        tab_samples_and_data.add(frame_sample_request, text='Sample Requests')
        tab_samples_and_data.add(frame_data_request, text='Data Requests')
        tab_samples_and_data.grid(row=3, column=1)

        # label to confirm sign-in and disable login button and username entry
        lbl_confirmation = Label(frame_user_info, text='...Connected!')
        lbl_confirmation.grid(row=1, column=3)
        btn_login.config(state='disabled')
        entry_uname.config(state='disabled')

    except request.RedcapError:
        # handle REDCap error, incorrect token
        messagebox.showerror('Error', 'Incorrect API token for ' + api_key_uname)
    except:
        messagebox.showerror('Error', 'Invalid User')


def triple_match(df):
    # create column combining age, sex, and hla for grouping
    df['age_sex_hla'] = df['age'].astype(str) + '/' + df['gender'] + '/' + df['hla']

    # keep only duplicated groups
    df = df[df.duplicated(['age_sex_hla'], keep=False)]

    # group by the age/sex/hla combo and list the unique clinical statuses found
    group = df['clinical_status'].groupby(df['age_sex_hla']).unique().apply(pd.Series).reset_index(level=0)
    group[['age', 'sex', 'hla']] = group['age_sex_hla'].str.split('/', 2, expand=True)

    # account for num different clinical statuses requested
    cols = ['sex', 'age', 'hla', 'age_sex_hla']
    count = 0
    while count < len(cols):
        if count in group.columns:
            cols.append(count)
        count += 1
    group = group[cols]

    # take only rows with all clinical status columns filled; each group has all requested clinical statuses
    n = 0
    while n < len(group.columns):
        if n in group.columns:
            group = group.loc[group[n].notna()]
        n += 1

    # search master list for the age/sex combos
    search_me = group['age_sex_hla'].tolist()
    df = df[df['age_sex_hla'].isin(search_me)]
    return df


def double_match(df, params):
    # combine both parameters to match
    to_match = params[0] + '_' + params[1]

    # new column to combine both parameters to match, separated by a /
    df[to_match] = df[params[0]].astype(str) + '/' + df[params[1]].astype(str)

    df = df[df.duplicated([to_match], keep=False)]

    # account for num different clinical statuses requested
    group = df['clinical_status'].groupby(df[to_match]).unique().apply(pd.Series).reset_index(level=0)
    group[[params[0], params[1]]] = group[to_match].str.split('/', 1, expand=True)
    cols = [params[0], params[1], to_match]
    count = 0
    while count < len(cols):
        if count in group.columns:
            cols.append(count)
        count += 1

    # take only rows with all clinical status columns filled, every group has all requested clinical statuses
    n = 0
    while n < len(group.columns):
        if n in group.columns:
            group = group.loc[group[n].notna()]
        n += 1

    search_me = group[to_match].tolist()
    df = df[df[to_match].isin(search_me)]
    return df


def single_match(df, param):
    # only one parameter, save it as string to pass to df
    param = param[0]

    df = df[df.duplicated([param], keep=False)]

    # account for num different clinical statuses requested
    group = df['clinical_status'].groupby(df[param]).unique().apply(pd.Series).reset_index(level=0)
    cols = [param]
    count = 0
    while count < len(cols):
        if count in group.columns:
            cols.append(count)
        count += 1

    # take only rows with all clinical status columns filled, every group has all requested clinical statuses
    n = 0
    while n < len(group.columns):
        if n in group.columns:
            group = group.loc[group[n].notna()]
        n += 1

    search_me = group[param].tolist()
    df = df[df[param].isin(search_me)]
    return df


btn_login = Button(frame_user_info, text='Connect', command=login)
btn_login.grid(row=1, column=2, padx=10)

login_window.mainloop()
