#include <ros/ros.h>
#include <tf/transform_broadcaster.h>

#include "constants.hh"

int main(int argc, char** argv){
   ros::init(argc, argv, "hand_arm_tf_broadcaster");
   ros::NodeHandle node;

   tf::TransformBroadcaster br;
   tf::Transform transform;

   ros::Rate rate(10.0);
   while (node.ok()){
      transform = ARMTIP2HAND_TRANSFORM;
      //calibration from the arm_tip to the palm of the hand
      br.sendTransform( tf::StampedTransform( transform, ros::Time::now(), "hand_goal_pose", "armtip_goal_pose" ) );
      transform = ARMTIP2HAND_TRANSFORM.inverse();
      //calibration matrix used to compute the pose of the palm of the hand from the pose of the end of the arm
      br.sendTransform( tf::StampedTransform( transform, ros::Time::now(), "armtip_fwdK_pose", "hand_fwdK_pose" ) );
      transform = ARMBASE2W_TRANSFORM;
      //calibration matrix between the world based and staubli arm base
      br.sendTransform( tf::StampedTransform( transform, ros::Time::now(), "world", "armbase" ) );
      rate.sleep();
   }
   return 0;
};
