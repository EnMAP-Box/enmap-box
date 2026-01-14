def enmapboxApplicationFactory(enmapBox):
    """
    Returns a list of EnMAPBoxApplications
    :param enmapBox: the EnMAP-Box instance.
    :return: EnMAPBoxApplication | [list-of-EnMAPBoxApplications]
    """
    try:
        from enpt_enmapboxapp.enpt_enmapboxapp import EnPTEnMAPBoxApp
    except ModuleNotFoundError as ex:
        if ex.name == 'enpt_enmapboxapp':
            return []

    return [EnPTEnMAPBoxApp(enmapBox)]

