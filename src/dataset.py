#!/usr/bin/env python3


import os
import numpy as np
from tqdm import tqdm

import rosbag
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import Float64MultiArray
from sensor_msgs import point_cloud2 as pc2
from dca1000_device.msg import RadarCubeMsg
import rospy


def process_messages(dataset_dir, rdc_bag_filename, diff_bag_filename, rdc_topic, map_topic, odds_topic):  # rdc_messages, map_messages, odds_messages):
    rdc_bag = rosbag.Bag(os.path.join(dataset_dir, rdc_bag_filename))
    map_bag = rosbag.Bag(os.path.join(dataset_dir, diff_bag_filename))

    map_frames_idx, rdc_frames_idx = [], []
    map_iter = enumerate(map_bag.read_messages(topics=[map_topic]))
    map_idx, (_, map_msg, _) = next(map_iter)
    prev_time_diff = rospy.Duration.from_sec(99999999)

    for rdc_idx, (_, rdc_msg, _) in tqdm(enumerate(rdc_bag.read_messages(topics=[rdc_topic]))):
        while True:
            current_time_diff = abs(rdc_msg.header.stamp - map_msg.header.stamp)
            if current_time_diff < prev_time_diff:
                prev_time_diff = current_time_diff
                try:
                    map_idx, (_, map_msg, _) = next(map_iter)
                except StopIteration:
                    print('Finished MAP')
                    break
            else:
                rdc_frames_idx.append(rdc_idx)
                map_frames_idx.append(map_idx - 1)
                prev_time_diff = rospy.Duration.from_sec(99999999)
                break

    print(len(map_frames_idx), len(rdc_frames_idx))

    rdc_samples_list = []
    map_points_list = []
    odds_arrays_list = []
    for topic, msg, t in tqdm(rdc_bag.read_messages(topics=[rdc_topic])):
        rdc_samples = np.array(msg.samples)
        rdc_samples_list.append(rdc_samples)
    for topic, msg, t in tqdm(map_bag.read_messages(topics=[map_topic, odds_topic])):
        if topic == map_topic:
            point_generator = pc2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True)
            map_array = np.array(list(point_generator))
            map_points_list.append(map_array)
        elif topic == odds_topic:
            odds_array = np.array(msg.data)
            odds_arrays_list.append(odds_array)

    rdc_bag.close()
    map_bag.close()

    print(len(rdc_samples_list), len(map_points_list), len(odds_arrays_list))

    return 0, 0, 0
        # if map_msg.header.stamp
    # matched = []
    # j = 0
    # for i in range(len(messages1)):
    #     while j < len(messages2) and messages2[j].header.stamp < messages1[i].header.stamp:
    #         j += 1
    #     if j < len(messages2) and messages2[j].header.stamp == messages1[i].header.stamp:
    #         matched.append((messages1[i], messages2[j]))
    # return matched


def main(
        rdc_topic='/dca_node/data_cube',
        map_pcl_topic='/lidar_filtered/octomap_full/update/pcl_centered_full',
        map_odds_topic='/lidar_filtered/octomap_full/update/pcl_occupancy_odds'
):
    dataset_dir = 'mapping/coloradar'
    rdc_bag_filename = 'ec_hallways_run0.bag'
    diff_bag_filename = 'ec_hallways_run0_lidar_octomap_diff.bag'

    map_frames, map_odds, rdc_frames = process_messages(
        os.path.join(os.path.expanduser('~'), dataset_dir), rdc_bag_filename, diff_bag_filename,
        rdc_topic=rdc_topic, map_topic=map_pcl_topic, odds_topic=map_odds_topic
    )


if __name__ == "__main__":
    main()
    # parser = argparse.ArgumentParser(description="Adjust pointcloud sizes in a rosbag file.")
    # parser.add_argument("--file", type=str, help="Path to the rosbag file.")
    # parser.add_argument("--topic", type=str, help="Topic of the PointCloud2 messages.")
    # parser.add_argument("-N", type=int, help="Target number of points.")
    # args = parser.parse_args()
    #
    # main(args.bag_path, args.topic, args.target_points)