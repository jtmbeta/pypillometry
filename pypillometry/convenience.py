import numpy as np

def nprange(ar):
    return (ar.min(),ar.max())


import pystan
import pickle
from hashlib import md5

def zscale(y):
    return (y-np.nanmean(y))/np.nanstd(y)

def p_asym_laplac(y, mu, sigma, tau):
    """
    Asymmetric laplace distribution https://en.wikipedia.org/wiki/Asymmetric_Laplace_distribution;
    Parametrization as here: https://github.com/stan-dev/stan/issues/2312
    
    tau in [0,1]
    """
    I=np.array(y<=mu, dtype=np.int)
    return (2*tau*(1-tau))/sigma*np.exp(-2/sigma * ( (1-tau)*I*(mu-y) + tau*(1-I)*(y-mu) ) )

def p_asym_laplac_kappa(y, mu, lam, kappa):
    """
    Asymmetric laplace distribution https://en.wikipedia.org/wiki/Asymmetric_Laplace_distribution;
    Wikipedia parametrization.
    
    kappa in [0, infty] where 1 means symmetry
    """
    I=np.array(y<=mu, dtype=np.int)
    return (lam)/(kappa+1./kappa)*np.exp( ( (lam/kappa)*I*(y-mu) - lam*kappa*(1-I)*(y-mu) ) )


def trans_logistic_vec(x, a, b, inverse=False):
    """
    vectorized version of trans_logistic()
    
    goes from [a,b] to [-inf,+inf] and back;
    inverse=False: [a,b] -> [-inf, +inf]
    inverse=True:  [-inf,+inf] -> [a,b]
    if a or b is +/-infty, a logarithmic/exponential transform is used
    """
    eps=1e-15
    if inverse==False:
        # variables from [a,inf]
        x=np.where( (a>-np.infty) & (b==np.infty), np.log(np.maximum(x-a, eps)), x)
        # variables from [-inf, b]
        x=np.where( (a==-np.infty) & (b<np.infty), np.log(np.maximum(b-x, eps)), x)
        # variables from [a, b]
        x=np.where( (a>-np.infty) & (b<np.infty), -np.log( (b-a)/(x-a)-1 ), x)
    elif inverse==True:
        # variables from [-inf,inf] -> [a,inf]
        x=np.where( (a>-np.infty) & (b==np.infty), np.exp(x)+a, x)
        # variables from [-inf, inf] -> [-inf, b]
        x=np.where( (a==-np.infty) & (b<np.infty), b-np.exp(x), x)
        # variables from [-inf,inf] -> [a, b]
        x=np.where( (a>-np.infty) & (b<np.infty), (1./(1.+np.exp(-x)))*(b-a)+a, x)
    
    return x

def StanModel_cache(model_code, model_name=None, **kwargs):
    """Use just as you would `stan`"""
    code_hash = md5(model_code.encode('ascii')).hexdigest()
    if model_name is None:
        cache_fn = 'cached-model-{}.pkl'.format(code_hash)
    else:
        cache_fn = 'cached-{}-{}.pkl'.format(model_name, code_hash)
    try:
        sm = pickle.load(open(cache_fn, 'rb'))
    except:
        sm = pystan.StanModel(model_code=model_code)
        with open(cache_fn, 'wb') as f:
            pickle.dump(sm, f)
    else:
        print("Using cached StanModel")
    return sm


def plot_pupil_ipy(tx, sy, event_onsets=None, overlays=None, overlay_labels=None, figsize=(16,8)):
    """
    Plotting with interactive adjustment of plotting window.
    To use this, do

    $ pip install ipywidgets
    $ jupyter nbextension enable --py widgetsnbextension
    $ jupyter labextension install @jupyter-widgets/jupyterlab-manager

    """
    import pylab as plt
    from ipywidgets import interact, interactive, fixed, interact_manual, Layout
    import ipywidgets as widgets

    def draw_plot(plotxrange):
        xmin,xmax=plotxrange
        ixmin=np.argmin(np.abs(tx-xmin))
        ixmax=np.argmin(np.abs(tx-xmax))
        plt.figure(figsize=figsize)

        plt.plot(tx[ixmin:ixmax],sy[ixmin:ixmax])
        if overlays is not None:
            if type(overlays) is np.ndarray:
                plt.plot(tx[ixmin:ixmax],overlays[ixmin:ixmax],label=overlay_labels)
            else:
                for i,overlay in enumerate(overlays):
                    lab=overlay_labels[i] if overlay_labels is not None else None
                    plt.plot(tx[ixmin:ixmax],overlay[ixmin:ixmax], label=lab)
        plt.vlines(event_onsets, *plt.ylim(), color="grey", alpha=0.5)
        plt.xlim(xmin,xmax)
        if overlay_labels is not None:
            plt.legend()


    wid_range=widgets.FloatRangeSlider(
        value=[tx.min(), tx.max()],
        min=tx.min(),
        max=tx.max(),
        step=1,
        description=' ',
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=True,
        readout_format='.1f',
        layout=Layout(width='100%', height='80px')
    )

    interact(draw_plot, plotxrange=wid_range)