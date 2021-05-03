'''
This function is used to calculate the mean of all frames in the training dataset
    INPUTS:
      - dataset: the name of the dataset folder 
      - video_root_path: the folder that contains all the datasets
    OUTPUTS: 
        Saves the mean frame to a .npy file
'''
def calc_mean(dataset, video_root_path):
    import os
    from skimage.io import imread
    import numpy as np
    from skimage.transform import resize

    #path of the training frames
    frame_path = os.path.join(video_root_path, dataset, 'training_frames')
    count = 0
    frame_sum = None

    try:

      #loop on all the folders in the directory video_root_path/dataset/training_frames
        for frame_folder in os.listdir(frame_path):
          #exceptions related to our dataset
          if frame_folder == '.DS_Store' or frame_folder== '._.DS_Store':
            continue
          else:
            #loop on the frames in each folder video_root_path/dataset/training_frames/frame_folder        
            for frame_file in os.listdir(os.path.join(frame_path, frame_folder)):
              if frame_file == '.DS_Store' or frame_file== '._.DS_Store':
                continue
              else:
                #the frame's path
                frame_filename = os.path.join(frame_path, frame_folder, frame_file)
                #normalize frame
                frame_value = imread(frame_filename, as_gray=True, plugin='pil')/256
                #resize to (227,227)
                frame_value = resize(frame_value, (227, 227), mode='reflect')
                assert(0. <= frame_value.all() <= 1.)
                if frame_sum is None:
                  #intialze frame_sum
                    frame_sum = np.zeros(frame_value.shape).astype('float64')
                frame_sum += frame_value
                count += 1

    except Exception as e:
        print(e)
        pass
    #calculate the mean
    frame_mean = frame_sum / count
    assert(0. <= frame_mean.all() <= 1.)
    #save the mean frame to video_root_path/dataset/mean_frame_224.npy
    np.save(os.path.join(video_root_path, dataset, 'mean_frame_224.npy'), frame_mean)

'''

'''
def subtract_mean(dataset, video_root_path, is_combine=False):
    import os
    import yaml
    from skimage.io import imread
    import numpy as np
    from skimage.transform import resize
    
    def add_noise(data, noise_factor):
      import numpy as np
      noisy_data = data + noise_factor * np.random.normal(loc=0.0, scale=1.0, size=data.shape)
      return noisy_data

    frame_mean = np.load(os.path.join(video_root_path, dataset, 'mean_frame_224.npy'))
    training_combine = []
    testing_combine = []

    with open('config.yml', 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    is_clip = cfg.get('clip')
    noise_factor = cfg.get('noise_factor')

    frame_path = os.path.join(video_root_path, dataset, 'training_frames')
    for frame_folder in os.listdir(frame_path):
      if frame_folder == '.DS_Store' or frame_folder== '._.DS_Store':
        continue
      else:
        print('==> ' + os.path.join(frame_path, frame_folder))
        training_frames_vid = []
        for frame_file in sorted(os.listdir(os.path.join(frame_path, frame_folder))):
          if frame_file == '.DS_Store' or frame_file == '._.DS_Store':
            continue
          else:
            frame_filename = os.path.join(frame_path, frame_folder, frame_file)
            frame_value = imread(frame_filename, as_grey=True, plugin='pil')/256
            frame_value = resize(frame_value, (227, 227), mode='reflect')
            assert(0. <= frame_value.all() <= 1.)
            frame_value -= frame_mean
            training_frames_vid.append(frame_value)
        training_frames_vid = np.array(training_frames_vid)

        if noise_factor is not None and noise_factor > 0:
            training_frames_vid = add_noise(training_frames_vid, noise_factor)
        if is_clip is not None and is_clip:
            training_frames_vid = np.clip(training_frames_vid, 0, 1)

        np.save(os.path.join(video_root_path, dataset, 'training_frames_{}.npy'.format(frame_folder[-3:])), training_frames_vid)
        if is_combine:
            training_combine.extend(training_frames_vid.reshape(-1, 227, 227, 1))

    frame_path = os.path.join(video_root_path, dataset, 'testing_frames')
    for frame_folder in os.listdir(frame_path):
      if frame_folder == '.DS_Store' or frame_folder== '._.DS_Store' or frame_folder.endswith('_gt') or not frame_folder.startswith('Test'):
        continue
      else:
        print('==> ' + os.path.join(frame_path, frame_folder))
        testing_frames_vid = []
        for frame_file in sorted(os.listdir(os.path.join(frame_path, frame_folder))):
          if frame_file == '.DS_Store' or frame_file== '._.DS_Store':
            continue
          else:
            frame_filename = os.path.join(frame_path, frame_folder, frame_file)
            try:
              frame_value = imread(frame_filename, as_grey=True, plugin='pil')/256
            except:
              print("Error in: ",frame_file)
              continue
            frame_value = resize(frame_value, (227, 227), mode='reflect')
            assert(0. <= frame_value.all() <= 1.)
            frame_value -= frame_mean
            testing_frames_vid.append(frame_value)
        testing_frames_vid = np.array(testing_frames_vid)

        if noise_factor is not None and noise_factor > 0:
            testing_frames_vid = add_noise(testing_frames_vid, noise_factor)
        if is_clip is not None and is_clip:
            testing_frames_vid = np.clip(testing_frames_vid, 0, 1)

        np.save(os.path.join(video_root_path, dataset, 'testing_frames_{}.npy'.format(frame_folder[-3:])), testing_frames_vid)
        if is_combine:
            testing_combine.extend(testing_frames_vid.reshape(-1, 160, 240, 1))
    if is_combine:
        training_combine = np.array(training_combine)
        testing_combine = np.array(testing_combine)
        np.save(os.path.join(video_root_path, dataset, 'training_frames_t0.npy'), training_combine)
        np.save(os.path.join(video_root_path, dataset, 'testing_frames_t0.npy'), testing_combine)

def build_h5(dataset, train_or_test, t, video_root_path):
    import h5py
    from tqdm import tqdm
    import os
    import numpy as np

    print("==> {} {}".format(dataset, train_or_test))

    def build_volume(train_or_test, num_videos, time_length):
        for i in tqdm(range(num_videos)):
            data_frames = np.load(os.path.join(video_root_path, '{}/{}_frames_{:03d}.npy'.format(dataset, train_or_test, i+1)))
            data_frames = np.expand_dims(data_frames, axis=-1)
            num_frames = data_frames.shape[0]

            data_only_frames = np.zeros((num_frames-time_length, time_length, 227, 227, 1)).astype('float64')

            vol = 0
            for j in range(num_frames-time_length):
                data_only_frames[vol] = data_frames[j:j+time_length] # Read a single volume
                vol += 1

            with h5py.File(os.path.join(video_root_path, '{0}/{1}_h5_t{2}/{0}_{3:02d}.h5'.format(dataset, train_or_test, time_length, i+1)), 'w') as f:
                if train_or_test == 'Train':
                    np.random.shuffle(data_only_frames)
                f['data'] = data_only_frames

    
    os.makedirs(os.path.join(video_root_path, '{}/{}_h5_t{}'.format(dataset, train_or_test, t)), exist_ok=True)
    num_videos = len(os.listdir(os.path.join(video_root_path, '{}/{}'.format(dataset, train_or_test))))-1
    build_volume(train_or_test, num_videos, time_length=t)

def combine_dataset(dataset, t, video_root_path='VIDEO_ROOT_PATH'):
    import h5py
    import os
    from tqdm import tqdm

    print("==> {}".format(dataset))
    output_file = h5py.File(os.path.join(video_root_path, '{0}/{0}_train_t{1}.h5'.format(dataset, t)), 'w')
    h5_folder = os.path.join(video_root_path, '{0}/training_h5_t{1}'.format(dataset, t))
    filelist = sorted([os.path.join(h5_folder, item) for item in os.listdir(h5_folder)])


    # keep track of the total number of rows
    total_rows = 0

    for n, f in enumerate(tqdm(filelist)):
      your_data_file = h5py.File(f, 'r')
      your_data = your_data_file['data']
      total_rows = total_rows + your_data.shape[0]

      if n == 0:
        # first file; create the dummy dataset with no max shape
        create_dataset = output_file.create_dataset('data', (total_rows, t, 160, 240, 1), maxshape=(None, t, 227, 227, 1))
        # fill the first section of the dataset
        create_dataset[:,:] = your_data
        where_to_start_appending = total_rows

      else:
        # resize the dataset to accomodate the new data
        create_dataset.resize(total_rows, axis=0)
        create_dataset[where_to_start_appending:total_rows, :] = your_data
        where_to_start_appending = total_rows

    output_file.close()


def preprocess_data(logger, dataset, t, video_root_path):
    import os
    import yaml

    with open('config.yml', 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    data_regen = False
    if cfg.get('data-regen'):
        data_regen = cfg['data-regen']

    # Step 1: Calculate the mean frame of all training frames
    # Check if mean frame file exists for the dataset
    # If the file exists, then we can skip re-generating the file
    # Else calculate and generate mean file
    logger.debug("Step 1/4: Check if mean frame exists for {}".format(dataset))
    mean_frame_file = os.path.join(video_root_path, dataset, 'mean_frame_224.npy')
    training_frame_path = os.path.join(video_root_path, dataset, 'training_frames')
    testing_frame_path = os.path.join(video_root_path, dataset, 'testing_frames')
    if not os.path.isfile(mean_frame_file):
        # The frames must have already been extracted from training and testing videos
        assert(os.path.isdir(training_frame_path))
        assert(os.path.isdir(testing_frame_path))
        logger.info("Step 1/4: Calculating mean frame for {}".format(dataset))
        calc_mean(dataset, video_root_path)

    # Step 2: Subtract mean frame from each training and testing frames
    # Check if training & testing frames are already been subtracted
    # If the file exists, then we can skip re-generating the file
    logger.debug("Step 2/4: Check if training/testing_frames_videoID.npy exists for {}".format(dataset))
    try:
        if data_regen:
            raise AssertionError
        # try block will execute without AssetionError if all frames have been subtracted
        for frame_folder in os.listdir(training_frame_path):
            training_frame_npy = os.path.join(video_root_path, dataset, 'training_frames_{}.npy'.format(frame_folder[-3:]))
            assert(os.path.isfile(training_frame_npy))
        for frame_folder in os.listdir(testing_frame_path):
            testing_frame_npy = os.path.join(video_root_path, dataset, 'testing_frames_{}.npy'.format(frame_folder[-3:]))
            assert (os.path.isfile(testing_frame_npy))
    except AssertionError:
        # if all or some frames have not been subtracted, then generate those files
        logger.info("Step 2/4: Subtracting mean frame for {}".format(dataset))
        subtract_mean(dataset, video_root_path, t<=0)
    if t > 0:
        # Step 3: Generate small video volumes from the mean-subtracted frames and dump into h5 files (grouped by video ID)
        # Check if those h5 files have already been generated
        # If the file exists, then skip this step
        logger.debug("Step 3/4: Check if individual h5 files exists for {}".format(dataset))
        for train_or_test in ('Train', 'Test'):
            try:
                h5_folder = os.path.join(video_root_path, '{}/{}_h5_t{}'.format(dataset, train_or_test, t))
                assert(os.path.isdir(h5_folder))
                num_videos = len(os.listdir(os.path.join(video_root_path, '{}/{}'.format(dataset, train_or_test))))
                for i in range(num_videos):
                    h5_file = os.path.join(video_root_path, '{0}/{1}_h5_t{2}/{0}_{3:02d}.h5'.format(dataset, train_or_test, t, i+1))
                    assert(os.path.isfile(h5_file))
            except AssertionError:
                logger.info("Step 3/4: Generating volumes for {} {} set".format(dataset, train_or_test))
                build_h5(dataset, train_or_test, t, video_root_path)

        # Step 4: Combine small h5 files into one big h5 file
        # Check if this big h5 file is already been generated
        # If the file exists, then skip this step
        logger.debug("Step 4/4: Check if individual h5 files have already been combined for {}".format(dataset))
        training_h5 = os.path.join(video_root_path, '{0}/{0}_train_t{1}.h5'.format(dataset, t))
        if not os.path.isfile(training_h5):
            logger.info("Step 4/4: Combining h5 files for {}".format(dataset))
            combine_dataset(dataset, t, video_root_path)

    logger.info("Preprocessing is completed")