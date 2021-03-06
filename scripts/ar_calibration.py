import roslib
roslib.load_manifest('calibration')
roslib.load_manifest('ar_pose')
roslib.load_manifest('trajectory_planner')
import rospy
from tf import transformations as tr
import tf
import tf_conversions.posemath as pm
from numpy import pi, eye, dot, cross, linalg, sqrt, ceil, size
from numpy import hstack, vstack, mat, array, arange, fabs, zeros
import opencv
import math
import staubli_tx60.msg
import staubli_tx60.srv
import actionlib
from trajectory_planner import *
from std_msgs.msg import Empty

def TransformIntersection( T_set ): 
    """Given a set of transforms that are rotations around a point,
    estimate that point
    See http://en.wikipedia.org/wiki/Line-line_intersection
    """
    v_set = list()
    p_set = list()
    for T in T_set:
        phi, S, point = pm.transformations.rotation_from_matrix(T)
        p_set.append(array([point]).transpose())
        v_set.append(array([S]).transpose())
    m1 = zeros([3,1])
    m2 = zeros([3,3])
    for k in range(len(p_set)):
        a = eye(3) - dot(v_set[k], v_set[k].transpose())
        m1 += dot(a , p_set[k][:3])
        m2 += a
    return dot(linalg.inv(m2),m1)

def get_staubli_cartesian_as_pose_msg():
    rospy.wait_for_service('getCartesian')
    try:
        get_cartesian = rospy.ServiceProxy( 'getCartesian', staubli_tx60.srv.GetCartesian )
        resp1 = get_cartesian()
        # make srv x y z  rx ry rz euler angle representation into pose message
        pos = geometry_msgs.msg.Point( x = resp1.x, y = resp1.y, z = resp1.z )
        q = tf.transformations.quaternion_from_euler( resp1.rx , resp1.ry, resp1.rz ,'rxyz' )
        quat =  geometry_msgs.msg.Quaternion( x = q[0], y = q[1], z = q[2], w = q[3] )
        return geometry_msgs.msg.Pose( position = pos, orientation = quat )
    except rospy.ServiceException, e:
        print "Service call failed: %s"%e
        return []

def get_staubli_cartesian_as_tran():
    current_pose = get_staubli_cartesian_as_pose_msg()
    return pm.toMatrix(pm.fromMsg(current_pose))
    

def rotate_wrist(angle, direction):
    """Given an angle and a direction in the robot frame, move the wrist
    by that angle at it's current position
    """
    current_tran = get_staubli_cartesian_as_tran()
    #rotate around current position
    rotation_tran = pm.transformations.rotation_matrix(angle, direction,current_tran[:3,3])
    desired_tran = dot(rotation_tran, current_tran)
    SendCartesianGoal(desired_tran, True)

def get_ar_tran_dict():
    """Return the homogeneous transforms of the various ar markers
    in a dictionary of homogeneous transforms
    """

def GetTFAsMatrix(parent_frame, child_frame):
    listener = tf.TransformListener()
    return pm.toMatrix(pm.fromTf(listener.lookupTransform(parent_frame, child_frame, rospy.Time.now())))

def GetWristPositionInCamera(angle_mag):
    """Move the wrist around three axes to extract the transform from wrist to camera
    from the visual markers
    param angle_mag - magnitude by which to rotate wrist around hand
    """
    hand_tran = dict()
    marker_tran = dict()
    marker_tf_name =  '/test_cvtfbcaster_tf'
    hand_tran['home_tran'] = get_staubli_cartesian_as_tran()
    marker_tran['home_tran'] = GetTFAsMatrix('usb_cam',marker_tf_name)
    rotate_wrist(angle_mag, [1,0,0])
    hand_tran['x_rot'] = get_staubli_cartesian_as_tran()
    marker_tran['x_rot'] = GetTFAsMatrix('usb_cam',marker_tf_name)
    rotate_wrist(-angle_mag, [1,0,0])
    rotate_wrist(angle_mag, [0,1,0])
    hand_tran['y_rot'] = get_staubli_cartesian_as_tran()
    marker_tran['y_rot'] = GetTFAsMatrix('usb_cam',marker_tf_name) 
    rotate_wrist(-angle_mag, [0,1,0])
    rotate_wrist(angle_mag, [0,0,1])
    hand_tran['z_rot'] = get_staubli_cartesian_as_tran()
    marker_tran['z_rot'] = GetTFAsMatrix('usb_cam',marker_tf_name)
    rotate_wrist(-angle_mag, [0,0,1])
    
    def get_rel_tran(tran_dict, key):
        return dot(linalg.inv(tran_dict['home_tran']), tran_dict[key])

    def get_rel_tran_list(tran_dict):
        tf_list = list()
        tf_list.append(get_rel_tran(tran_dict, 'x_rot'))
        tf_list.append(get_rel_tran(tran_dict, 'y_rot'))
        tf_list.append(get_rel_tran(tran_dict, 'z_rot'))

    hand_tran_list = get_rel_tran_list(hand_tran)
    marker_tran_list = get_rel_tran_list(marker_tran)
    wrist_tran_camera = zeros((4,4))
    wrist_tran_camera[:3,3] = TransformIntersection(marker_tran_list)
    for i in range(3):
        unused, wrist_tran_camera[:3,i], unused2 = pm.transformations.rotation_from_matrix(marker_tran_list[i])

    return wrist_tran_camera


def GetCameraPose():
    marker_tf_name = '/test_cvtfbcaster_tf'
    listener = tf.TransformListener()
    return listener.lookupTransform(marker_tf_name, '/usb_cam', rospy.Time(0))

class CameraPosePublisher(object):
    def __init__(self):
        self.cam_pose = []
        self.tf_publisher = tf.TransformBroadcaster()
        self.rate = rospy.Rate(10.0)
        self.update_cam_service = rospy.Service('update_cam_pose', Empty, self.update_camera_pose)
        self.update_cam_pose()
    def run(self):
        while not rospy.is_shutdown():
            self.tf_publisher.sendTransform(self.cam_pose[0], self.cam_pose[1],
                                        rospy.Time.now(),
                                        "/usb_cam", "/world")
            rate.sleep()
    def update_camera_pose(self, msg = []):
        self.cam_pose = GetCameraPose()                        


def GetBarrettPositionInCamera(angle_mag):
    listener = tf.TransformListener()

temp_tf3 = ((0.1087, -0.042950000000000002, 0.0), array([ 0.        ,  0.        ,  0.70710678,  0.70710678]))
arm_in_robot = get_staubli_cartesian_as_tran()
bc.sendTransform(temp_tf3[0], temp_tf3[1], rospy.Time.now(), "/temp2_tf","/checkerboard")
offset_arm_in_world_tf = li.lookupTransform('/world','/temp2_tf', rospy.Time(0))
offset_arm_in_world = pm.toMatrix(pm.fromTf(offset_arm_in_world_tf))
robot_in_world = np.dot(offset_arm_in_world,np.linalg.inv(arm_in_robot))
    
    
