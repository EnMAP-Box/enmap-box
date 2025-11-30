def enmapboxApplicationFactory(enmapBox):
    """
    Returns a list of EnMAPBoxApplications
    :param enmapBox: the EnMAP-Box instance.
    :return: EnMAPBoxApplication | [list-of-EnMAPBoxApplications]
    """
    try:
        from enfrosp_enmapboxapp.enfrosp_enmapboxapp import EnFROSPEnMAPBoxApp
    except ModuleNotFoundError as ex:
        if ex.name == 'enfrosp_enmapboxapp':
            return []

    return [EnFROSPEnMAPBoxApp(enmapBox)]
