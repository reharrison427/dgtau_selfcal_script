import glob


'''
##### Copy backup into original file
#rmtables('calibrated_final.ms')
#os.system('rm -rf calibrated_final.ms.flagversions')
os.system('cp -r calibrated_final.ms.backup calibrated_final.ms')

##### Average all windows and split
rmtables('calibrated_source_4spw.ms')
os.system('rm -rf calibrated_source_4spw.ms.flagversions')
split(vis='calibrated_final.ms', outputvis='calibrated_source_4spw.ms', spw='0~3', datacolumn='data', width=[64,64,64,64], field='DG_Tauri')

##### Make 4spw backup
rmtables('calibrated_source_4spw.ms.backup')
os.system('cp -r calibrated_source_4spw.ms calibrated_source_4spw.ms.backup')
'''



##### Copy averaged backup into original file
rmtables('calibrated_source_4spw.ms')
os.system('rm -rf calibrated_source_4spw.ms.flagversions')
os.system('cp -r calibrated_source_4spw.ms.backup calibrated_source_4spw.ms')

# 4 averaged windows
contvis  = 'calibrated_source_4spw.ms'

# Interactive data reduction?
interactive=True




#--------------------------------------------------------------------------------------#
# start:              Self-calibration of continuum sources                            #
# -------------------------------------------------------------------------------------#

# Beam = 0.63" x 0.52"
cell = '0.04arcsec' 

# Weighting
weighting = 'briggs'
robust = 1

# Refant
refant = 'DV04' 

# 4 continnum spectral windows, 2 GHz each
spwmap = [0,0,0,0]
spw='0,1,2,3'



#######################################
# CLEAN IM Lup
#######################################

# Field name
field = 'DG_Tauri'
# Name of selfcal calibration tables
caltablename = 'DG_Tauri'
# Image size
imsize = [256,256] 
# Continuum image name
contimagename = 'DG_Tauri_cont_image'
# Continuum mask name
#mask = 'circle[[225pix,225pix],40pix]'

# NOISE LEVELS (mJy)
# Source    I        Q,U      POLI
# IMLup	    7.5e-5   1.5e-5   2e-5

# Thresholds:

#threshold_0 = '1e-3Jy'

# threshold_final_I = 2*sigma_I in the final CLEANed map
#threshold_final_I = '1.5e-4Jy'

# threshold_final_QUV = 2*sigma_Q,U in the final CLEANed maps
#threshold_final_QUV = '3e-5Jy'

# polithresh = 3*sigma in the POLI map
#polithresh = '6e-5Jy/beam'

# Limiting polarization fraction: 1.5/7.5 * 0.3 = 0.6%

##### SELFCAL ITERATION PARAMETERS

p0 = { 'imagename' : contimagename+'_p0',
       'niter' : 200,
       'threshold' : threshold_0,
       'spwmap' : spwmap,
       'uvrange_clean' : '',
       'stokes' : ['I'],
       'deconvolver' : 'hogbom'
       }
 
p1 = { 'imagename' : contimagename+'_p1',
       'caltable' : 'pcal1_'+caltablename,
       'niter' : 500,
       'calmode' : 'p',
       'gaintype' : 'T', # Average XX and YY gain solutions for higher SNR
       'solint' : 'inf',
       'threshold_I' : threshold_0,
       'spwmap' : spwmap,
       'uvrange_gaincal' : '',
       'uvrange_clean' : '',
       'stokes' : ['I'],
       'deconvolver' : 'hogbom'
       }
 
p2 = { 'imagename' : contimagename+'_p2',
       'caltable' : 'pcal2_'+caltablename,
       'niter' : 1000,
       'calmode' : 'p',
       'gaintype' : 'T', # Average XX and YY gain solutions for higher SNR
       'solint' : '30.25s',
       'threshold_I' : threshold_0,
       'spwmap' : spwmap,
       'uvrange_gaincal' : '',
       'uvrange_clean' : '',
       'stokes' : ['I'],
       'deconvolver' : 'hogbom'
       }
 
##### NOTE gaintype='G' AND stokes='IQUV' MODEL

# After solving for and applying pcal3 solution, _p3 CLEANs the IQUV image
p3 = { 'imagename' : contimagename+'_p3',
       'caltable' : 'pcal3_'+caltablename,
       'niter' : 100000, 
       'calmode' : 'p',
       'gaintype' : 'G', # Solve for gains for each polarization separately
       'solint' : '15s',
       'threshold_I' : threshold_final_I,
       'spwmap' : spwmap,
       'uvrange_gaincal' : '',
       'uvrange_clean' : '',
       'stokes' : ['IQUV'],
       'deconvolver' : 'hogbom'
       }

# The final iteration solves for a super-short-interval pcal solution using the full IQUV cube as a model; then it makes the final IQUV image.
pol = { 'imagename' : contimagename,
	'caltable' : 'pcal4_'+caltablename,
	'niter' : 100000, 
	'calmode' : 'p',
	'gaintype' : 'G', # Solve for gains for each polarization separately
	'solint' : '10s',
	'threshold_I' : threshold_final_I,
	'threshold_QUV' : threshold_final_QUV,
	'spwmap' : spwmap,
	'uvrange_gaincal' : '',
	'uvrange_clean' : '',
	'stokes' : ['I','Q','U','V'],
	'deconvolver' : 'hogbom'
	}

ap = { 'imagename' : contimagename+'_ap',
       'caltable' : 'apcal_'+caltablename,
       'gaintable' : 'pcal3_'+caltablename, # Apply final pcal solution on the fly
       'niter' : 100000, 
       'calmode' : 'ap',
       'gaintype' : 'G', # Solve for gains for each polarization separately
       'solint' : 'inf', # Length of each scan (~2 min)
       'threshold_I' : threshold_final_I,
       'threshold_QUV' : threshold_final_QUV,
       'spwmap' : spwmap,
       'uvrange_gaincal' : '',
       'uvrange_clean' : '',
       'stokes' : ['I','Q','U','V'],
       'deconvolver' : 'hogbom',
       }



##### SELFCAL ITERATIONS

clearcal(vis=contvis)
delmod(vis=contvis)

for iteration in [p0, p1, p2, p3, pol] :

    if iteration == p0 :
 
	# For consistent notation with the rest of the iterations
	s = iteration['stokes'][0]

	# Initial CLEAN
	for ext in ['.image','.mask','.model','.pb','.psf','.residual','.sumwt']:
	    # os.system('rm -rf ' + iteration['imagename'] + ext)
	    rmtables(iteration['imagename'] + ext)

	tclean(vis=contvis,
	       field=field,
	       imagename=iteration['imagename'],
	       cell=cell,
	       imsize=imsize,
	       stokes=s,
	       deconvolver=iteration['deconvolver'],
	       outframe='BARY',
	       specmode='mfs',
	       spw=spw,
	       mask=mask,
	       #threshold=iteration['threshold'],
	       niter=iteration['niter'],
	       weighting=weighting,
	       robust=robust,
	       interactive=interactive,
               savemodel='modelcolumn',
	)

    # Run full gaincal -- applycal -- CLEAN loop
    else :

	# For apcal
	if iteration == ap :
	    # SELFCAL amplitude solutions
	    os.system('rm -rf {0}'.format(iteration['caltable']))
	    gaincal(vis=contvis,
		    caltable=iteration['caltable'], # Produce this caltable
		    field=field,
		    gaintype=iteration['gaintype'], # DON'T combine two polarizations for apcal
		    gaintable=iteration['gaintable'], # Apply the final pcal solution on the fly
		    # combine='spw', # For better SNR in gain solution
		    solnorm=False, # "True" normalizes average solutions to 1
		    refant=refant, 
		    calmode=iteration['calmode'],
		    solint=iteration['solint'],
		    uvrange=iteration['uvrange_gaincal'],
		    minsnr=3.0,
		    minblperant=6)

	else :
	    # SELFCAL phase solutions
	    os.system('rm -rf {0}'.format(iteration['caltable']))
	    gaincal(vis=contvis,
		    caltable=iteration['caltable'],
		    field=field,
		    gaintype=iteration['gaintype'],
		    # combine='spw', # For better SNR in gain solution
		    refant=refant, 
		    calmode=iteration['calmode'],
		    solint=iteration['solint'],
		    uvrange=iteration['uvrange_gaincal'],
		    minsnr=3.0,
		    minblperant=6)

	# Apply corrections
	applycal(vis=contvis,
		 field=field,
		 spwmap=iteration['spwmap'], 
		 gaintable=iteration['caltable'],
		 calwt=F, 
		 flagbackup=F)

	# Continue CLEANing

	# Clean appropriately based on desired Stokes parameters
	for s in iteration['stokes'] :

	    # Define correct imagename
	    if iteration == pol or iteration == ap :
		imagename = iteration['imagename']+'_{0}'.format(s)
	    else :
		imagename = iteration['imagename']

	    # Remove previous files
            for ext in ['.image','.mask','.model','.pb','.psf','.residual','.sumwt']:
		# os.system('rm -rf ' + iteration['imagename'] + ext)
		rmtables(imagename + ext)

	    # Define thresholds
	    if s == 'Q' or s == 'U' or s == 'V' :
		threshold = iteration['threshold_QUV']
	    else :
		threshold = iteration['threshold_I']

            tclean(vis=contvis,
                   field=field,
                   imagename=imagename, # Changed
                   cell=cell,
                   imsize=imsize,
                   stokes=s,
                   deconvolver=iteration['deconvolver'],
                   outframe='BARY',
                   specmode='mfs',
                   spw=spw,
                   #threshold=threshold, # Changed
                   niter=iteration['niter'],
                   weighting=weighting,
                   robust=robust,
                   mask=mask,
                   interactive=interactive,
                   savemodel='modelcolumn',
            )




##### Polarization images production	    

# Polarized intensity
os.system('rm -rf {0}_POLI.image'.format(contimagename))
immath(outfile=contimagename+'_POLI.image',
       mode='poli',
       imagename=[contimagename+'_Q.image', contimagename+'_U.image'],
       sigma='0.0Jy/beam')

# Polarization angle
os.system('rm -rf {0}_POLA.image'.format(contimagename))
immath(outfile=contimagename+'_POLA.image',
       mode='pola',
       imagename=[contimagename+'_Q.image', contimagename+'_U.image'],
       polithresh=polithresh)

# Polarization fraction
os.system('rm -rf {0}_PFRAC.image'.format(contimagename))
immath(outfile=contimagename+'_PFRAC.image',
       mode='evalexpr',
       imagename=[contimagename+'_POLI.image', contimagename+'_I.image'],
       expr='(IM0/IM1)')

# Primary beam correction
for image in ['I', 'Q', 'U', 'V', 'POLI', 'POLA', 'PFRAC'] :
    os.system('rm -rf {0}_{1}.pbcor'.format(contimagename, image))
    impbcor(imagename=contimagename+'_{0}.image'.format(image), 
            pbimage=contimagename+'_I.pb'.format(image),
            outfile=contimagename+'_{0}.pbcor'.format(image))

    ##### Make FITS files of final .image files as well as .pbcor files
    os.system('rm -rf {0}_{1}.pbcor.fits'.format(contimagename, image) )
    exportfits(imagename=contimagename+'_{0}.pbcor'.format(image),
	       fitsimage=contimagename+'_{0}.pbcor.fits'.format(image))


'''

# Code for separating individual Stokes images
     for stokes_image in ['I', 'Q', 'U', 'V'] :
         single_image = pol['imagename'].strip('IQUV')+stokes_image+'.image'
         primary_beam = pol['imagename'].strip('IQUV')+stokes_image+'.flux'
         # os.system('rm -rf {0} {1}'.format(single_image, primary_beam))
         rmtables(primary_beam)
         rmtables(single_image)
         immath(imagename=pol['imagename']+'.image', outfile=single_image, expr='IM0', stokes=stokes_image)
         immath(imagename=pol['imagename']+'.flux', outfile=primary_beam, expr='IM0', stokes=stokes_image)
'''
