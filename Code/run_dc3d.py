# Running dc3d, given an input namedtuple.


import numpy as np 
import matplotlib.pyplot as plt 
import collections
import sys
from okada_wrapper import dc3dwrapper
import conversion_math

# NOTES:
Input_object = collections.namedtuple('Input_object',
	['PR1','FRIC','depth','start_gridx', 'finish_gridx', 'start_gridy', 'finish_gridy', 'xinc', 'yinc', 'minlon','maxlon','zerolon','minlat','maxlat','zerolat','source_object','receiver_object'])
Faults_object = collections.namedtuple('Faults_object',['xstart','xfinish','ystart','yfinish','Kode','rtlat','reverse','strike','dipangle','rake','top','bottom','comment']);
Out_object = collections.namedtuple('Out_object',
	['x','y','x2d','y2d','u_disp','v_disp','w_disp']);

def do_stress_computation(params, inputs):
	# Step 0. Split receiver fault into many sub-faults if necessary
	# Step 1. Compute strains and displacements
	# Step 2. Resolve stresses on receiver faults
	split_subfaults(params, inputs);
	[x, y, x2d, y2d, u_displacements, v_displacements, w_displacements] = compute_surface_disp(params, inputs);

	[] = compute_strains_stresses(params, inputs);

	MyOutObject = Out_object(x=x,y=y,x2d=x2d, y2d=y2d, u_disp=u_displacements, v_disp=v_displacements, w_disp=w_displacements);  
	# this object will have more outputs tomorrow, like strains and stresses. 

	return MyOutObject;


def split_subfaults(params,inputs):
	rec_faults=inputs.receiver_object;
	for i in range(len(rec_faults.xstart)):
		# We have a receiver fault. 
		# In the future, we may want to split this up using params. 
		# This is not well integrated right now. 
		print("Receiver faults not split yet.")
	return;


def compute_surface_disp(params, inputs):

	x=np.linspace(inputs.start_gridx,inputs.finish_gridx,(inputs.finish_gridx-inputs.start_gridx)/inputs.xinc);
	y=np.linspace(inputs.start_gridy,inputs.finish_gridy,(inputs.finish_gridy-inputs.start_gridy)/inputs.yinc);
	[x2d,y2d] = np.meshgrid(x,y);
	u_displacements = np.zeros((len(x), len(y)));
	v_displacements = np.zeros((len(x), len(y)));
	w_displacements = np.zeros((len(x), len(y)));
	numrows=np.shape(u_displacements)[0]
	numcols=np.shape(u_displacements)[1]


	for i in range(len(inputs.source_object.xstart)):
	# A major compute loop for each source object. 

		# Fault parameters
		L = conversion_math.get_strike_length(inputs.source_object.xstart[i],inputs.source_object.xfinish[i],inputs.source_object.ystart[i],inputs.source_object.yfinish[i]);
		W = conversion_math.get_downdip_width(inputs.source_object.top[i],inputs.source_object.bottom[i],inputs.source_object.dipangle[i]);
		depth       = inputs.source_object.top[i];
		strike      = inputs.source_object.strike[i];
		dip         = inputs.source_object.dipangle[i];
		strike_slip = inputs.source_object.rtlat[i];
		dip_slip    = inputs.source_object.reverse[i];		

		# Preparing to rotate to a fault-oriented coordinate system.
		theta=inputs.source_object.strike[i]-90;
		theta=np.deg2rad(theta);
		R=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
		R2=np.array([[np.cos(-theta),-np.sin(-theta)],[np.sin(-theta),np.cos(-theta)]])
 
		for ky in range(numrows):
			for kx in range(numcols):

				# Compute the position relative to the translated, rotated fault. 
				translated_pos = np.array([[x2d[ky][kx]-inputs.source_object.xstart[i]],[y2d[ky][kx]-inputs.source_object.ystart[i]]]);
				xy=R.dot(translated_pos);
				success, u, grad_u = dc3dwrapper(params.alpha, [xy[0], xy[1], 0.0], depth, dip, [0, L], [-W, 0], [strike_slip, dip_slip, 0.0]);  # solve for displacements at the surface
				urot=R2.dot(np.array([[u[0]], [u[1]]]));

				# Update the displacements from all sources 
				u_displacements[ky][kx]=u_displacements[ky][kx] + urot[0];
				v_displacements[ky][kx]=v_displacements[ky][kx] + urot[1];
				w_displacements[ky][kx]=w_displacements[ky][kx] + u[2];  # vertical


	# OUTPUT GRIDS AND DISPLACEMENTS
	return [x, y, x2d, y2d, u_displacements, v_displacements, w_displacements];
	

def get_receiver_center(receiver_object):
	center = [0,0,0]; 
	# Will fix tomorrow.
	return center; 


def compute_strains_stresses(params, inputs):

	# Pseudocode: 
	# For each receiver, at the center point, sum up the strain and stress for each source.
	# Return an object with: receiver fault corners x, y, z, fault center x, y, z, rake, shear stress, normal stress, and coulomb stress. 
	# This is an important function. 

	number_of_receivers=len(inputs.receiver_object.xstart);
	
	# A few variables for asthetic use in plotting later. 
	receiver_corners_x=[];
	receiver_corners_y=[];
	receiver_corners_z=[];  # WILL POPULATE TOMORROW. 
	receiver_center_x=[];
	receiver_center_y=[];
	receiver_center_z=[];
	receiver_rake=[];

	# The values we're actually going to output. 
	receiver_shear=[];
	receiver_normal=[];
	receiver_coulomb=[];


	for m in range(number_of_receivers):
		centercoords = get_receiver_center(inputs.receiver_object[m]);
		receiver_center_x.append(centercoords[0]);
		receiver_center_y.append(centercoords[1]);
		receiver_center_z.append(centercoords[2]);

		for i in range(len(inputs.source_object.xstart)):
		# A major compute loop for each source object. 

			L = conversion_math.get_strike_length(inputs.source_object.xstart[i],inputs.source_object.xfinish[i],inputs.source_object.ystart[i],inputs.source_object.yfinish[i]);
			W = conversion_math.get_downdip_width(inputs.source_object.top[i],inputs.source_object.bottom[i],inputs.source_object.dipangle[i]);
			depth       = inputs.source_object.top[i];
			strike      = inputs.source_object.strike[i];
			dip         = inputs.source_object.dipangle[i];
			strike_slip = inputs.source_object.rtlat[i];
			dip_slip    = inputs.source_object.reverse[i];

			# Preparing to rotate to a fault-oriented coordinate system.
			theta=inputs.source_object.strike[i]-90;
			theta=np.deg2rad(theta);
			R=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
			R2=np.array([[np.cos(-theta),-np.sin(-theta)],[np.sin(-theta),np.cos(-theta)]])
			
			# Compute the position relative to the translated, rotated fault. 
			translated_pos = np.array([[centercoords[0]-inputs.source_object.xstart[i]],[centercoords[1]-inputs.source_object.ystart[i]]]);
			xy=R.dot(translated_pos);
			success, u, grad_u = dc3dwrapper(params.alpha, [xy[0], xy[1], 0.0], depth, dip, [0, L], [-W, 0], [strike_slip, dip_slip, 0.0]);  # solve for displacements at the surface
			urot=R2.dot(np.array([[u[0]], [u[1]]]));

			print(grad_u);
			rotated_grad_u=grad_u;  # FIX THIS TOMORROW.
			# Here I'm going to rotate grad_u back into the unprimed coordinates. 
			# Then rotate again into receiver coordinates. 
			strain_tensor=conversion_math.get_strain_tensor(rotated_grad_u);
			stress_tensor=conversion_math.get_stress_tensor(strain_tensor, params.lame1, params.mu);

			# Then compute shear, normal, and coulomb stresses. 
			[normal, shear, coulomb]=conversion_math.get_coulomb_stresses(stress_tensor,strike,inputs.receiver_object.rake[m],dip,inputs.FRIC);

	return []; 
	


"""



"""
