from typing import Optional, Sequence, Union, Dict

import numpy as np
import pandas as pd

from .utils import invert, find_cols, bin_scale, to_idx, _check_score_range_exception


def compute_questionnaire_scores(data: pd.DataFrame,
                                 score_dict: Dict[str, Union[Sequence[str], pd.Index]]) -> pd.DataFrame:
    df_scores = pd.DataFrame(index=data.index)
    for score, columns in score_dict.items():
        df_scores = df_scores.join(globals()[score.lower()](data[columns]))

    return df_scores


def psqi(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Pittsburgh Sleep Quality Index"""

    score_name = "PSQI"
    score_range = [0, 3]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # Subjective Sleep Quality
    ssq = data.filter(regex="06").iloc[:, 0]

    # Sleep Latency
    sl = data.filter(regex="02").iloc[:, 0]
    bin_scale(sl, bins=[0, 15, 30, 60], last_max=True, inplace=True)

    # Sleep Duration
    sd = data.filter(regex="04").iloc[:, 0]

    # Sleep Disturbances
    sdist = data.filter(regex="05").iloc[:, :]

    # Use of Sleep Medication
    sm = data.filter(regex="07").iloc[:, 0]

    # Daytime Dysfunction
    dd = data.filter(regex="0[89]").sum(axis=1)
    dd = bin_scale(dd, bins=[-1, 0, 2, 4], inplace=False, last_max=True)

    sl = sl + data.filter(regex="05a").iloc[:, 0]

    # Habitual Sleep Efficiency
    hse = (sd / data['HoursBed']) * 100.0

    sdist = sdist.drop([sdist.columns[0], sdist.columns[-2]], axis='columns')

    sd = invert(bin_scale(sd, bins=[0, 4.9, 6, 7], last_max=True, inplace=False), score_range=score_range,
                inplace=False)
    hse = invert(bin_scale(hse, bins=[0, 64, 74, 84], last_max=True, inplace=False), score_range=score_range,
                 inplace=False)
    sdist = sdist.sum(axis=1)
    sdist = bin_scale(sdist, bins=[-1, 0, 9, 18, 27], inplace=False)

    psqi_data = {
        score_name + '_SubjectiveSleepQuality': ssq,
        score_name + '_SleepLatency': sl,
        score_name + '_SleepDuration': sd,
        score_name + '_HabitualSleepEfficiency': hse,
        score_name + '_SleepDisturbances': sdist,
        score_name + '_UseSleepMedication': sm,
        score_name + '_DaytimeDysfunction': dd
    }

    data = pd.DataFrame(psqi_data, index=data.index)
    data[score_name + '_TotalIndex'] = data.sum(axis=1)
    return data


def mves(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Maastricht Vital Exhaustion Scale"""

    score_name = "MVES"
    score_range = [0, 2]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # Reverse scores 9, 14
    invert(data, cols=to_idx([9, 14]), score_range=score_range)
    return pd.DataFrame(data.sum(axis=1), columns=[score_name])


def tics_s(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Trier Inventory for Chronic Stress (Short Version)"""

    score_name = "TICS_S"
    score_range = [0, 4]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    idxs = {
        'WorkOverload': [1, 3, 21],
        'SocialOverload': [11, 18, 28],
        'PressureToPerform': [5, 14, 29],
        'WorkDiscontent': [8, 13, 24],
        'DemandsWork': [12, 16, 27],
        'PressureSocial': [6, 15, 22],
        'LackSocialRec': [2, 20, 23],
        'SocialTension': [4, 9, 26],
        'SocialIsolation': [19, 25, 30],
        'ChronicWorry': [7, 10, 17]
    }

    tics = {
        '{}_{}'.format(score_name, key): data.iloc[:, to_idx(idxs[key])].sum(axis=1) for key in idxs
    }

    tics[score_name] = data.sum(axis=1)

    return pd.DataFrame(tics, index=data.index)


def tics_l(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Trier Inventory for Chronic Stress (Long Version)"""

    score_name = "TICS_L"
    score_range = [0, 4]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    idxs = {
        'WorkOverload': [50, 38, 44, 54, 17, 4, 27, 1],  # Arbeitsüberlastung
        'SocialOverload': [39, 28, 49, 19, 7, 57],  # Soziale Überlastung
        'PressureToPerform': [23, 43, 32, 22, 12, 14, 8, 40, 30],  # Erfolgsdruck
        'WorkDiscontent': [21, 53, 10, 48, 41, 13, 37, 5],  # Unzufriedenheit mit der Arbeit
        'DemandsWork': [55, 24, 20, 35, 47, 3],  # Überforderung bei der Arbeit
        'LackSocialRec': [31, 18, 46, 2],  # Mangel an sozialer Anerkennung
        'SocialTension': [26, 15, 45, 52, 6, 33],  # Soziale Spannungen
        'SocialIsolation': [42, 51, 34, 56, 11, 29],  # Soziale Isolation
        'ChronicWorry': [36, 25, 16, 9]  # Chronische Besorgnis
    }

    tics = {
        '{}_{}'.format(score_name, key): data.iloc[:, to_idx(idxs[key])].sum(axis=1) for key in idxs
    }

    return pd.DataFrame(tics, index=data.index)


def pss(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Perceived Stress Scale"""

    score_name = "PSS"
    score_range = [0, 4]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # Reverse scores 4, 5, 7, 8
    invert(data, cols=to_idx([4, 5, 7, 8]), score_range=score_range)

    return pd.DataFrame(data.sum(axis=1), columns=[score_name])


def cesd(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Center for Epidemiological Studies Depression Scale"""

    score_name = "CESD"
    score_range = [0, 3]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # Reverse scores 4, 8, 12, 16
    invert(data, cols=to_idx([4, 8, 12, 16]), score_range=score_range)
    return pd.DataFrame(data.sum(axis=1), columns=[score_name])


def ghq(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """General Health Questionnaire"""

    score_name = "GHQ"
    score_range = [0, 3]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # Reverse scores 1, 3, 4, 7, 8, 12
    invert(data, cols=to_idx([1, 3, 4, 7, 8, 12]), score_range=score_range)
    return pd.DataFrame(data.sum(axis=1), columns=[score_name])


def hads(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Hospital Anxiety and Depression Scale"""

    score_name = "HADS"
    score_range = [0, 3]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # Reverse scores 2, 4, 6, 7, 12, 14
    invert(data, cols=to_idx([2, 4, 6, 7, 12, 14]), score_range=score_range)

    hads_data = {
        score_name: data.sum(axis=1),
        score_name + '_Anxiety': data.iloc[:, np.arange(1, len(data.columns) + 1, 2) - 1].sum(axis=1),
        score_name + '_Depression': data.iloc[:, np.arange(2, len(data.columns) + 1, 2) - 1].sum(axis=1)
    }
    return pd.DataFrame(hads_data, index=data.index)


def type_d_scale(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Type D Personality Scale"""

    score_name = "DS"
    score_range = [0, 4]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # Reverse scores 1, 3
    invert(data, cols=to_idx([1, 3]), score_range=score_range)

    idxs = {
        'NegativeAffect': [2, 4, 5, 7, 9, 12, 13],
        'SocialInhibition': [1, 3, 6, 8, 10, 11, 14]
    }

    ds = {'{}_{}'.format(score_name, key): data.iloc[:, to_idx(idxs[key])].sum(axis=1) for key in idxs}
    ds[score_name] = data.sum(axis=1)
    return pd.DataFrame(ds, index=data.index)


def rse(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Rosenberg Self-Esteem Inventory"""

    score_name = "RSE"
    score_range = [0, 3]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # Reverse scores 2, 5, 6, 8, 9
    invert(data, cols=to_idx([2, 5, 6, 8, 9]), score_range=score_range)
    return pd.DataFrame(data.sum(axis=1), columns=[score_name])


def scs(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Self-Compassion Scale
    https://www.academia.edu/2040459
    """

    score_name = "SCS"
    score_range = [1, 5]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # Reverse scores 1, 2, 4, 6, 8, 11, 13, 16, 18, 20, 21, 24, 25
    invert(data, cols=to_idx([1, 2, 4, 6, 8, 11, 13, 16, 18, 20, 21, 24, 25]), score_range=score_range)

    idxs = {
        'SelfKindness': [5, 12, 19, 23, 26],
        'SelfJudgment': [1, 8, 11, 16, 21],
        'CommonHumanity': [3, 7, 10, 15],
        'Isolation': [4, 13, 18, 25],
        'Mindfulness': [9, 14, 17, 22],
        'OverIdentified': [2, 6, 20, 24]
    }

    # SCS is a mean, not a sum score!
    scs_data = {
        '{}_{}'.format(score_name, key): data.iloc[:, to_idx(idxs[key])].mean(axis=1) for key in idxs
    }
    scs_data[score_name] = data.mean(axis=1)

    return pd.DataFrame(scs_data, index=data.index)


def rfis(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Romantic and Friendship Intimacy Scales"""

    score_name = "RFIS"
    score_range = [1, 5]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # Reverse scores 2, 6, 10, 14
    invert(data, cols=to_idx([2, 6, 10, 14]), score_range=score_range)

    # SCS is a mean, not a sum score!
    return pd.DataFrame(data.mean(axis=1), columns=[score_name])


def midi(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Midlife Development Inventory (MIDI) Sense of Control Scale"""

    score_name = "MIDI"
    score_range = [1, 7]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # Reverse scores 1, 2, 4, 5, 7, 9, 10, 11
    invert(data, cols=to_idx([1, 2, 4, 5, 7, 9, 10, 11]), score_range=score_range)

    # MIDI is a mean, not a sum score!
    return pd.DataFrame(data.mean(axis=1), columns=[score_name])


def tsgs(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Trait Shame and Guilt Scale"""

    score_name = "TSGS"
    score_range = [1, 5]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    idxs = {
        'Shame': [2, 5, 8, 11, 14],
        'Guilt': [3, 6, 9, 12, 15],
        'Pride': [1, 4, 7, 10, 13],
    }

    tsgs_data = {
        '{}_{}'.format(score_name, key): data.iloc[:, to_idx(idxs[key])].sum(axis=1) for key in idxs
    }

    return pd.DataFrame(tsgs_data, index=data.index)


def rmidips(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Revised Midlife Development Inventory (MIDI) Personality Scale"""

    score_name = "RMIDIPS"
    score_range = [1, 4]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # "most items need to be reverse scored before subscales are computed => reverse all"
    invert(data, score_range=score_range)

    # re-reverse scores 19, 24
    invert(data, cols=to_idx([19, 24]), score_range=score_range)

    idxs = {
        'Neuroticism': [3, 8, 13, 19],
        'Extraversion': [1, 6, 11, 23, 27],
        'Openness': [14, 17, 21, 22, 25, 28, 29],
        'Conscientiousness': [4, 9, 16, 24, 31],
        'Agreeableness': [2, 7, 12, 18, 26],
        'Agency': [5, 10, 15, 20, 30]
    }

    # RMIDIPS is a mean, not a sum score!
    rmidips_data = {
        '{}_{}'.format(score_name, key): data.iloc[:, to_idx(idxs[key])].mean(axis=1) for key in idxs
    }

    return pd.DataFrame(rmidips_data, index=data.index)


def lsq(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Life Stress Questionnaire
    0 = No Stress
    1 = Stress
    """

    score_name = "LSQ"
    score_range = [0, 1]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    lsq_data = {
        score_name + '_Partner': find_cols(data, contains="Partner")[0].sum(axis=1),
        score_name + '_Parent': find_cols(data, contains="Parent")[0].sum(axis=1),
        score_name + '_Child': find_cols(data, contains="Child")[0].sum(axis=1),
    }

    return pd.DataFrame(lsq_data, index=data.index)


def ctq(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Childhood Trauma Questionnaire"""

    score_name = "CTQ"
    score_range = [1, 5]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # reverse scores 2, 5, 7, 13, 19, 26, 28
    invert(data, cols=to_idx([2, 5, 7, 13, 19, 26, 28]), score_range=score_range)

    idxs = {
        'PhysicalAbuse': [9, 11, 12, 15, 17],
        'SexualAbuse': [20, 21, 23, 24, 27],
        'EmotionalNeglect': [5, 7, 13, 19, 28],
        'PhysicalNeglect': [1, 2, 4, 6, 26],
        'EmotionalAbuse': [3, 8, 14, 18, 25],
        'Validity': [10, 16, 22]
    }

    ctq_data = {
        '{}_{}'.format(score_name, key): data.iloc[:, to_idx(idxs[key])].sum(axis=1) for key in idxs
    }

    return pd.DataFrame(ctq_data, index=data.index)


def peat(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Pittsburgh Enjoyable Activities Test"""

    score_name = "PEAT"
    score_range = [0, 4]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    return pd.DataFrame(data.sum(axis=1), columns=[score_name])


def purpose_life(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Purpose in Life"""

    score_name = "PurposeLife"
    score_range = [1, 5]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # reverse scores 2, 3, 5, 6, 10
    invert(data, cols=to_idx([2, 3, 5, 6, 10]), score_range=score_range)

    # Purpose in Life is a mean, not a sum score!
    return pd.DataFrame(data.mean(axis=1), columns=[score_name])


def trait_rumination(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Trait Rumination
    0 = False (no rumination),
    1 = True (rumination)
    """

    score_name = "TraitRumination"
    score_range = [0, 1]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    return pd.DataFrame(data.sum(axis=1), columns=[score_name])


def body_esteem(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Body-Esteem Scale for Adolescents and Adults"""

    score_name = "BodyEsteem"
    score_range = [0, 4]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # reverse scores 4, 7, 9, 11, 13, 17, 18, 19, 21
    invert(data, cols=to_idx([4, 7, 9, 11, 13, 17, 18, 19, 21]), score_range=score_range)

    idxs = {
        'Appearance': [1, 6, 9, 7, 11, 13, 15, 17, 21, 23],
        'Weight': [3, 4, 8, 10, 16, 18, 19, 22],
        'Attribution': [2, 5, 12, 14, 20],
    }

    # BE is a mean, not a sum score!
    be = {
        '{}_{}'.format(score_name, key): data.iloc[:, to_idx(idxs[key])].mean(axis=1) for key in idxs
    }
    be[score_name] = data.mean(axis=1)

    return pd.DataFrame(be, index=data.index)


def fscr(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Forms of Self-Criticizing/Attacking and Self-Reassuring Scale"""

    score_name = "FSCR"
    score_range = [0, 4]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    idxs_fscr = {
        'InadequateSelf': [1, 2, 4, 6, 7, 14, 17, 18, 20],
        'HatedSelf': [9, 10, 12, 15, 22],
        'ReassuringSelf': [3, 5, 8, 11, 13, 16, 19, 21],
    }

    fscr_data = {
        '{}_{}'.format(score_name, key): data.iloc[:, to_idx(idxs_fscr[key])].sum(axis=1) for key in idxs_fscr
    }

    return pd.DataFrame(fscr_data, index=data.index)


def pasa(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Primary Appraisal Secondary Appraisal Scale"""

    score_name = "PASA"
    score_range = [1, 6]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # reverse scores 1, 6, 7, 9, 10
    invert(data, cols=to_idx([1, 6, 7, 9, 10]), score_range=score_range)

    idxs_pasa = {
        'Threat': [1, 9, 5, 13],
        'Challenge': [6, 10, 2, 14],
        'SelfConcept': [7, 3, 11, 15],
        'ControlExp': [4, 8, 12, 16]
    }

    pasa_data = {
        '{}_{}'.format(score_name, key): data.iloc[:, to_idx(idxs_pasa[key])].sum(axis=1) for key in idxs_pasa
    }

    pasa_data[score_name + '_Primary'] = pasa_data[score_name + '_Threat'] + pasa_data[score_name + '_Challenge']
    pasa_data[score_name + '_Secondary'] = pasa_data[score_name + '_SelfConcept'] + pasa_data[
        score_name + '_ControlExp']
    pasa_data[score_name + '_StressComposite'] = pasa_data[score_name + '_Primary'] - pasa_data[
        score_name + '_Secondary']

    return pd.DataFrame(pasa_data, index=data.index)


def ssgs(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """State Shame and Guilt Scale"""


    score_name = "SSGS"
    score_range = [1, 5]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    idxs_ssgs = {
        'Pride': [1, 4, 7, 10, 13],
        'Shame': [2, 5, 8, 11, 14],
        'Guilt': [3, 6, 9, 12, 15],
    }

    ssgs_data = {
        '{}_State{}'.format(score_name, key): data.iloc[:, to_idx(idxs_ssgs[key])].sum(axis=1) for key in idxs_ssgs
    }

    return pd.DataFrame(ssgs_data, index=data.index)


def panas(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None,
          questionnaire_version: Optional[str] = 'german') -> pd.DataFrame:
    """
    Positive and Negative Affect Schedule

    NOTE: This implementation expects scores in the range [1, 5].

    Parameters
    ----------
    data
    columns
    questionnaire_version

    Returns
    -------

    """
    score_name = "PANAS"
    score_range = [1, 5]
    supported_versions = ['english', 'german']

    if questionnaire_version not in supported_versions:
        raise AttributeError(
            "questionnaire_version must be one of {}, not {}.".format(supported_versions, questionnaire_version))

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    if questionnaire_version == 'english':
        idx_panas = [2, 4, 6, 7, 8, 11, 13, 15, 18, 20]
    elif questionnaire_version == 'german':
        # German Version has other item indices
        idx_panas = [2, 5, 7, 8, 9, 12, 14, 16, 19, 20]
    else:
        idx_panas = []

    df_panas = {
        score_name + '_NegativeAffect': data.iloc[:, to_idx(idx_panas)].sum(axis=1)
    }
    df_panas[score_name + '_PositiveAffect'] = data.sum(axis=1) - df_panas[score_name + '_NegativeAffect']
    df_panas[score_name + '_Total'] = df_panas[score_name + '_PositiveAffect'] + invert(
        data.iloc[:, to_idx(idx_panas)],
        score_range=score_range,
        inplace=False).sum(axis=1)

    return pd.DataFrame(df_panas, index=data.index)


def state_rumination(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """State Rumination"""

    score_name = "StateRumination"
    score_range = [0, 4]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # reverse scores 1, 6, 9, 12, 15, 17, 18, 20, 27
    invert(data, cols=to_idx([1, 6, 9, 12, 15, 17, 18, 20, 27]), score_range=score_range)

    state_rum = {
        score_name: data.sum(axis=1)
    }

    return pd.DataFrame(state_rum, index=data.index)


# HABIT DATASET

def abi(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Angstbewältigungsinventar"""

    score_name = "ABI"
    score_range = [1, 2]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # split into 8 subitems, consisting of 10 questions each
    items = np.split(data, 8, axis=1)
    abi_raw = pd.concat(items, keys=np.arange(1, len(items) + 1), axis=1)
    idx_kov = {
        # ABI-P
        2: [2, 3, 7, 8, 9],
        4: [1, 4, 5, 8, 10],
        6: [2, 3, 5, 6, 7],
        8: [2, 4, 6, 8, 10],
        # ABI-E
        1: [2, 3, 6, 8, 10],
        3: [2, 4, 5, 7, 9],
        5: [3, 4, 5, 9, 10],
        7: [1, 5, 6, 7, 9],
    }
    idx_kov = {key: np.array(idx_kov[key]) for key in idx_kov}
    idx_vig = {key: np.setdiff1d(np.arange(1, 11), np.array(idx_kov[key]), assume_unique=True) for key in idx_kov}
    abi_kov, abi_vig = [pd.concat([abi_raw.loc[:, key].iloc[:, idx[key] - 1] for key in idx], axis=1,
                                  keys=abi_raw.columns.unique(level=0)) for idx in [idx_kov, idx_vig]]

    abi_data = {
        score_name + "_KOV-T": abi_kov.sum(axis=1),
        score_name + "_VIG-T": abi_vig.sum(axis=1),
        score_name + "_KOV-P": abi_kov.loc[:, [2, 4, 6, 8]].sum(axis=1),
        score_name + "_VIG-P": abi_vig.loc[:, [2, 4, 6, 8]].sum(axis=1),
        score_name + "_KOV-E": abi_kov.loc[:, [1, 3, 5, 7]].sum(axis=1),
        score_name + "_VIG-E": abi_vig.loc[:, [1, 3, 5, 7]].sum(axis=1),
    }

    return pd.DataFrame(abi_data, index=data.index)


def stadi(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """State-Trait-Angst-Depressions-Inventar"""

    score_name = "STADI"
    score_range = [1, 4]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    if len(data.columns) == 10:
        # only STADI-State-Anxiety
        stadi_data = dict()
        for subsc, idx in zip(["AU", "BE"],
                              [[1, 3, 5, 7, 9], [2, 4, 6, 9, 10]]):
            stadi_data['{}_State_{}'.format(score_name, subsc)] = data.iloc[:, to_idx(idx)].sum(axis=1)
        df_stadi = pd.DataFrame(stadi_data, index=data.index)
        df_stadi['{}_State_Anxiety'.format(score_name)] = stadi_data["{}_State_AU".format(score_name)] + stadi_data[
            "{}_State_BE".format(score_name)]
        return df_stadi
    elif len(data.columns) == 20:
        st = ["State"]
    else:
        st = ["State", "Trait"]

    # split into n subitems (either State or State and Trait)
    items = np.split(data, len(st), axis=1)
    data = pd.concat(items, keys=st, axis=1)

    idx_stadi = {
        'AU': [1, 5, 9, 13, 17],
        'BE': [2, 6, 10, 14, 18],
        'EU': [3, 7, 11, 15, 19],
        'DY': [4, 8, 12, 16, 20]
    }

    stadi_data = dict()
    for s in st:
        for key in idx_stadi:
            stadi_data['{}_{}_{}'.format(score_name, s, key)] = data[s].iloc[:, to_idx(idx_stadi[key])].sum(axis=1)

    df_stadi = pd.DataFrame(stadi_data, index=data.index)

    dict_meta = {'{}_{}_Anxiety'.format(score_name, sub): stadi_data["{}_{}_AU".format(score_name, sub)] + stadi_data[
        "{}_{}_BE".format(score_name, sub)] for sub in st}

    dep = {'{}_{}_Depression'.format(score_name, sub): stadi_data["{}_{}_EU".format(score_name, sub)] + stadi_data[
        "{}_{}_DY".format(score_name, sub)] for sub in st}
    dict_meta.update(dep)

    total = {'{}_{}_Total'.format(score_name, sub): dict_meta["{}_{}_Anxiety".format(score_name, sub)] + dict_meta[
        "{}_{}_Depression".format(score_name, sub)] for sub in st}
    dict_meta.update(total)

    df_meta = pd.DataFrame(dict_meta, index=data.index)
    df_meta = df_meta.reindex(sorted(df_meta.columns), axis='columns')

    # join dataframe of subscores and meta scores
    return df_stadi.join(df_meta)


def svf_120(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Stressverarbeitungsfragebogen - 120 items

    NOTE: This implementation expects a score range of [1, 5].
    """

    score_name = "SVF120"
    score_range = [1, 5]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    idx_svf = {
        'Bag': [10, 31, 50, 67, 88, 106],  # Bagatellisierung
        'Her': [17, 38, 52, 77, 97, 113],  # Herunterspielen
        'Schab': [5, 30, 43, 65, 104, 119],  # Schuldabwehr
        'Abl': [1, 20, 45, 86, 101, 111],  # Ablenkung
        'Ers': [22, 36, 64, 74, 80, 103],  # Ersatzbefriedigung
        'Sebest': [34, 47, 59, 78, 95, 115],  # Selbstbestätigung
        'Entsp': [12, 28, 58, 81, 99, 114],  # Entspannung
        'Sitkon': [11, 18, 39, 66, 91, 116],  # Situationskontrolle
        'Rekon': [2, 26, 54, 68, 85, 109],  # Reaktionskontrolle
        'Posi': [15, 37, 56, 71, 83, 96],  # Positive Selbstinstruktion
        'Sozube': [3, 21, 42, 63, 84, 102],  # Soziales Unterstützungsbedürfnis
        'Verm': [8, 29, 48, 69, 98, 118],  # Vermeidung
        'Flu': [14, 24, 40, 62, 73, 120],  # Flucht
        'Soza': [6, 27, 49, 76, 92, 107],  # Soziale Abkapselung
        'Gedw': [16, 23, 55, 72, 100, 110],  # Gedankliche Weiterbeschäftigung
        'Res': [4, 32, 46, 60, 89, 105],  # Resignation
        'Selmit': [13, 41, 51, 79, 94, 117],  # Selbstbemitleidung
        'Sesch': [9, 25, 35, 57, 75, 87],  # Selbstbeschuldigung
        'Agg': [33, 44, 61, 82, 93, 112],  # Aggression
        'Pha': [7, 19, 53, 70, 90, 108],  # Pharmakaeinnahme
    }
    svf = {
        "{}_{}".format(score_name, key): data.iloc[:, to_idx(idx_svf[key])].sum(axis=1) for key in idx_svf
    }

    svf = pd.DataFrame(svf, index=data.index)

    names = ["Pos1", "Pos2", "Pos3", "Pos_Gesamt", "Neg_Gesamt"]
    subscales = [('Bag', 'Her', 'Schab'),
                 ('Abl', 'Ers', 'Sebest', 'Entsp'),
                 ('Sitkon', 'Rekon', 'Posi'),
                 ('Bag', 'Her', 'Schab', 'Abl', 'Ers', 'Sebest', 'Entsp', 'Sitkon', 'Rekon', 'Posi'),
                 ('Flu', 'Soza', 'Gedw', 'Res', 'Selmit', 'Sesch')
                 ]

    for n, subsc in zip(names, subscales):
        svf["{}_{}".format(score_name, n)] = svf[["{}_{}".format(score_name, s) for s in subsc]].mean(axis=1)

    return svf


def svf_42(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Stressverarbeitungsfragebogen - 42 items"""

    score_name = "SVF42"
    score_range = [1, 5]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    idx_svf = {
        'Bag': [7, 22],  # Bagatellisierung
        'Her': [11, 35],  # Herunterspielen
        'Schab': [2, 34],  # Schuldabwehr
        'Abl': [1, 32],  # Ablenkung
        'Ers': [12, 42],  # Ersatzbefriedigung
        'Sebest': [19, 37],  # Selbstbestätigung
        'Entsp': [13, 26],  # Entspannung
        'Sitkon': [4, 23],  # Situationskontrolle
        'Rekon': [17, 33],  # Reaktionskontrolle
        'Posi': [9, 24],  # Positive Selbstinstruktion
        'Sozube': [14, 27],  # Soziales Unterstützungsbedürfnis
        'Verm': [6, 30],  # Vermeidung
        'Flu': [16, 40],  # Flucht
        'Soza': [20, 29],  # Soziale Abkapselung
        'Gedw': [10, 25],  # Gedankliche Weiterbeschäftigung
        'Res': [38, 15],  # Resignation
        'Hilf': [18, 28],  # Hilflosigkeit
        'Selmit': [8, 31],  # Selbstbemitleidung
        'Sesch': [21, 36],  # Selbstbeschuldigung
        'Agg': [3, 39],  # Aggression
        'Pha': [5, 41],  # Pharmakaeinnahme
    }
    svf = {
        "{}_{}".format(score_name, key): data.iloc[:, to_idx(idx_svf[key])].sum(axis=1) for key in idx_svf
    }

    svf = pd.DataFrame(svf, index=data.index)

    names = ["Denial", "Distraction", "Stressordevaluation"]
    subscales = [('Flu', 'Verm', 'Soza'), ('Ers', 'Entsp', 'Sozube'), ('Bag', 'Her', 'Posi')]

    for n, subsc in zip(names, subscales):
        svf["{}_{}".format(score_name, n)] = svf[["{}_{}".format(score_name, s) for s in subsc]].mean(axis=1)

    return svf


def brief_cope(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Brief-COPE - 28 items"""

    score_name = "BriefCope"
    score_range = [1, 4]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    idx_cope = {
        'Self_Distraction': [1, 19],  # Ablenkung
        'Active_Coping': [2, 7],  # Aktive Bewältigung
        'Denial': [3, 8],  # Verleugnung
        'Substance_Use': [4, 11],  # Alkohol/Drogen
        'Emotional_Support': [5, 15],  # Emotionale Unterstützung
        'Instrumental_Support': [10, 23],  # Instrumentelle Unterstützung
        'Behavioral_Disengagement': [6, 16],  # Verhaltensrückzug
        'Venting': [9, 21],  # Ausleben von Emotionen
        'Pos_Reframing': [12, 17],  # Positive Umdeutung
        'Planning': [14, 25],  # Planung
        'Humor': [18, 28],  # Humor
        'Acceptance': [20, 24],  # Akzeptanz
        'Religion': [22, 27],  # Religion
        'Self_Blame': [13, 26],  # Selbstbeschuldigung
    }
    cope = {
        "{}_{}".format(score_name, key): data.iloc[:, to_idx(idx_cope[key])].sum(axis=1) for key in idx_cope
    }

    return pd.DataFrame(cope, index=data.index)


def bfi_k(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Big Five Inventory - Kurzversion"""

    score_name = "BFI-K"
    score_range = [1, 5]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # invert items 1, 2, 8, 9, 11, 12, 17, 21
    invert(data, cols=to_idx([1, 2, 8, 9, 11, 12, 17, 21]), score_range=score_range)

    idx_bfik = {
        'E': [1, 6, 11, 16],  # Extraversion
        'V': [2, 7, 12, 17],  # Verträglichkeit
        'G': [3, 8, 13, 18],  # Gewissenhaftigkeit
        'N': [4, 9, 14, 19],  # Neurotizismus
        'O': [5, 10, 15, 20, 21],  # Offenheit für neue Erfahrungen
    }

    bfik = {
        "{}_{}".format(score_name, key): data.iloc[:, to_idx(idx_bfik[key])].mean(axis=1) for key in idx_bfik
    }

    return pd.DataFrame(bfik, index=data.index)


def rsq(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Response Styles Questionnaire"""

    score_name = "RSQ"
    score_range = [1, 4]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    idx_rsq = {
        'SympRum': [2, 3, 4, 8, 11, 12, 13, 25],  # Symptomfokussierte Rumination
        'SelbstRum': [1, 19, 26, 28, 30, 31, 32],  # Selbstfokussierte Rumination
        'Distract': [5, 6, 7, 9, 14, 16, 18, 20],  # Distraktion
    }

    rsq_data = {
        "{}_{}".format(score_name, key): data.iloc[:, to_idx(idx_rsq[key])].mean(axis=1) for key in idx_rsq
    }
    rsq_data = pd.DataFrame(rsq_data, index=data.index)

    # invert items 5, 6, 7, 9, 14, 16, 18, 20 to add "Distract" subscale to total score
    rsq_data["{}_{}".format(score_name, 'Distract')] = \
        invert(data, cols=to_idx(idx_rsq['Distract']),
               score_range=score_range,
               inplace=False).iloc[:, to_idx(idx_rsq['Distract'])].mean(axis=1)
    rsq_data[score_name] = pd.DataFrame(rsq_data, index=data.index).mean(axis=1)
    return rsq_data


def sss(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Subjektiver Sozialer Status"""

    score_name = "SSS"
    score_range = [1, 10]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    return pd.DataFrame(data.sum(axis=1), columns=[score_name])


def fkk(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Fragebogen zur Kompetenz- und Kontrollüberzeugungen"""

    score_name = "FKK"
    score_range = [1, 6]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # invert items 4, 8, 12, 24
    invert(data, cols=to_idx([4, 8, 12, 24]), score_range=score_range)

    # Primärskalenwerte
    idx_fkk = {
        'SK': [4, 8, 12, 24, 16, 20, 28, 32],
        'I': [1, 5, 6, 11, 23, 25, 27, 30],
        'P': [3, 10, 14, 17, 19, 22, 26, 29],
        'C': [2, 7, 9, 13, 15, 18, 21, 31],
    }
    fkk_data = {
        "{}_{}".format(score_name, key): data.iloc[:, to_idx(idx_fkk[key])].sum(axis=1) for key in idx_fkk
    }
    fkk_data = pd.DataFrame(fkk_data, index=data.index)

    # Sekundärskalenwerte
    fkk_data[score_name + "_SKI"] = fkk_data[score_name + '_SK'] + fkk_data[score_name + '_I']
    fkk_data[score_name + "_PC"] = fkk_data[score_name + '_P'] + fkk_data[score_name + '_C']
    # Tertiärskalenwerte
    fkk_data[score_name + "_SKI_PC"] = fkk_data[score_name + '_SKI'] - fkk_data[score_name + '_PC']

    return fkk_data


def bidr(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Balanced Inventory of Desirable Responding"""

    score_name = "BIDR"
    score_range = [1, 7]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # invert items 2, 4, 5, 7, 9, 10, 11, 12, 14, 15, 17, 18, 20 => invert all and re-invert the others
    invert(data, score_range=score_range)
    invert(data, cols=to_idx([1, 3, 6, 8, 13, 16, 19]), score_range=score_range)

    idx_bidr = {
        'ST': np.arange(1, 11),  # Selbsttäuschung
        'FT': np.arange(11, 21),  # Fremdtäuschung
    }

    bidr_data = {
        "{}_{}".format(score_name, key): data.iloc[:, to_idx(idx_bidr[key])].sum(axis=1) for key in idx_bidr
    }
    return pd.DataFrame(bidr_data, index=data.index)


def kkg(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Kontrollüberzeugungen zu Krankheit und Gesundheit"""

    score_name = "KKG"
    score_range = [1, 6]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    idx_kkg = {
        'I': [1, 5, 8, 16, 17, 18, 21],
        'P': [2, 4, 6, 10, 12, 14, 20],
        'C': [3, 7, 9, 11, 13, 15, 19]
    }

    kkg_data = {
        score_name + "_" + key: data.iloc[:, to_idx(idx_kkg[key])].sum(axis=1) for key in idx_kkg
    }
    return pd.DataFrame(kkg_data, index=data.index)


def thoughts_questionnaire(data: pd.DataFrame,
                           columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Thoughts Questionnaire"""

    score_name = "Thoughts"
    score_range = [1, 5]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # invert items 1, 6, 9, 12, 15, 17, 18, 20, 27
    invert(data, cols=to_idx([1, 6, 9, 12, 15, 17, 18, 20, 27]), score_range=score_range)
    return pd.DataFrame(data.sum(axis=1), columns=[score_name])


def fee(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None,
        questionnaire_version: Optional[str] = 'german') -> pd.DataFrame:
    """Fragebogen zum erinnerten elterlichen Erziehungsverhalten"""

    score_name = "FEE"
    score_range = [1, 4]
    supported_versions = ['english', 'german']

    if questionnaire_version not in supported_versions:
        raise AttributeError(
            "questionnaire_version must be one of {}, not {}.".format(supported_versions, questionnaire_version))

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    df_mother = pd.DataFrame()
    df_father = pd.DataFrame()
    if questionnaire_version == 'german':
        df_mother = data.filter(like="Mutter").copy()
        df_father = data.filter(like="Vater").copy()
    elif questionnaire_version == 'english':
        df_mother = data.filter(like="Mother").copy()
        df_father = data.filter(like="Father").copy()

    idx_fee = {
        'Ablehnung_Strafe': [1, 3, 6, 8, 16, 18, 20, 22],
        'Emot_Waerme': [2, 7, 9, 12, 14, 15, 17, 24],
        'Kontrolle': [4, 5, 10, 11, 13, 19, 21, 23],
    }

    fee_mother = {
        "{}_{}_Mother".format(score_name, key): df_mother.iloc[:, to_idx(idx_fee[key])].mean(axis=1) for key in idx_fee
    }
    fee_father = {
        "{}_{}_Father".format(score_name, key): df_father.iloc[:, to_idx(idx_fee[key])].mean(axis=1) for key in idx_fee
    }
    fee_mother.update(fee_father)

    return pd.DataFrame(fee_mother, index=data.index)


def mbi(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Maslach Burnout Inventory"""

    score_name = "MBI"
    score_range = [1, 6]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    mbi_type = data.iloc[:, 0] - 1
    mbi_type.name = "{}_Type".format(score_name)
    data.drop(axis=1, labels=data.columns[0], inplace=True)
    # MBI in HABIT was assessed in the regular and Student form,
    # depending on the subject => 2 questionnaires, split into 2 dataframes
    items = np.split(data, 2, axis=1)
    for i in [0, 1]:
        items[i] = items[i][mbi_type == i]
        items[i].columns = items[0].columns
    data = pd.concat(items).sort_index()

    idx_mbi = {
        'EmotErsch': [1, 2, 3, 4, 5],
        'PersErf': [6, 7, 8, 11, 12, 16],
        'Deperson': [9, 10, 13, 14, 15],
    }

    mbi_data = {
        "{}_{}".format(score_name, key): data.iloc[:, to_idx(idx_mbi[key])].mean(axis=1) for key in idx_mbi
    }

    data = pd.DataFrame(mbi_data, index=data.index)
    data[mbi_type.name] = mbi_type
    return data


def mlq(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Meaning in Life Questionnaire"""

    score_name = "MLQ"
    score_range = [1, 7]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # invert item 9
    invert(data, cols=to_idx([9]), score_range=score_range)

    idx_mlq = {
        'PresenceMeaning': [1, 4, 5, 6, 9],
        'SearchMeaning': [2, 3, 7, 8, 10],
    }

    mlq_data = {
        "{}_{}".format(score_name, key): data.iloc[:, to_idx(idx_mlq[key])].mean(axis=1) for key in idx_mlq
    }
    return pd.DataFrame(mlq_data, index=data.index)


def ceca(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Childhood Experiences of Care and Abuse"""

    score_name = "CECA"

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    ceca_data = [
        data.filter(like="Q3_05"),
        data.filter(like="Q3_07"),
        data.filter(like="Q3_09"),
        data.filter(like="Q3_12").iloc[:, to_idx([5, 6])],
        data.filter(like="Q3_13"),
        data.filter(like="Q3_16").iloc[:, to_idx([5, 6])]
    ]

    ceca_data = pd.concat(ceca_data, axis=1).sum(axis=1)
    return pd.DataFrame(ceca_data, index=data.index, columns=[score_name])


def pfb(data: pd.DataFrame, columns: Optional[Union[Sequence[str], pd.Index]] = None) -> pd.DataFrame:
    """Partnerschaftsfragebogen"""

    score_name = "PFB"
    score_range = [1, 4]

    if columns:
        # if columns parameter is supplied: slice columns from dataframe
        data = data[columns]

    _check_score_range_exception(data, score_range)

    # invert item 19
    invert(data, cols=to_idx([19]), score_range=score_range)

    idx_pfb = {
        'Zaertlichkeit': [2, 3, 5, 9, 13, 14, 16, 23, 27, 28],
        'Streitverhalten': [1, 6, 8, 17, 18, 19, 21, 22, 24, 26],
        'Gemeinsamkeit': [4, 7, 10, 11, 12, 15, 20, 25, 29, 30],
        'Glueck': [31]
    }

    pfb_data = {
        "{}_{}".format(score_name, key): data.iloc[:, to_idx(idx_pfb[key])].sum(axis=1) for key in idx_pfb
    }

    pfb_data[score_name] = data.iloc[:, 0:30].sum(axis=1)
    return pd.DataFrame(pfb_data, index=data.index)
