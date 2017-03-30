# -*- coding: utf-8 -*-
"""
Created on Fri Mar 17 05:58:03 2017
Small tool to organize data and results of a neuro imaging pipeline.
Handles CSV XLS and ListLines files.

@author: vradduru
"""

import json
import os
import pandas

#%%

def load_json(filepath):
    with open(filepath,'rt') as f:
        output = json.load(f)
    return output


        
def create_project(project_dir, project_fileheader):
        """
        """
        if not os.path.isdir(project_dir):
            raise IOError("Project path must be an existing directory")
        return FolderNode(project_dir,project_fileheader)
    
    
    
    
class _Node(object):
                    
    def __init__(self, node_dir, project_name, **kwargs):

        self.__get_nodeinfo(node_dir,project_name,**kwargs)
        self.__create_properties(**kwargs)
        
        
    def __get_nodeinfo(self,node_dir,project_name,**kwargs):
        
        if 'node_info' in kwargs.keys():
            node_info = kwargs.get('node_info')
            if not (isinstance(node_info, dict) or \
                    isinstance(node_info, unicode)):
                raise TypeError("node_info: must be a dictionary or string")
        else:
            node_info = {}
            
        if isinstance(node_info, unicode):
            node_info = {'Type': node_info}
            
        nodeinfo_filepath = os.path.join(node_dir, project_name+'.gdm')
        node_info.update({'path':node_dir})
        
        try:
            if os.path.isfile(nodeinfo_filepath):
                node_info.update(load_json(nodeinfo_filepath))
        
        except Exception as e:
            raise type(e)(e.message + '\n When loading node_info from file: '+ nodeinfo_filepath)
            
        self._node_info = node_info
        
     
    def __create_properties(self,**kwargs):
        
        node_props = self._node_info.keys()
        if 'hprops' in kwargs.keys():
            hprops = kwargs['hprops']
        else :
            hprops = []
        
        for prop in node_props:
            if prop in hprops :
                continue
            setattr(self,prop,self._node_info[prop])
            
    def _load_subjects(self):
        
        try:
            self.__sub_list
        
        except AttributeError:
            sublist_filename = os.path.join(self._node_info['path'],
                                            self._node_info['Subjects'])
        
            with open(sublist_filename,'rt') as f:
                lines = f.readlines()
            subjects = [k.rstrip() for k in lines]
        
        setattr(self,'Subjects',subjects)
        
    def get_subject_data(self,items,subjects = None,routeselection=None):
        
        if routeselection == None and isinstance(items,list):
            routeselection = [None]*len(items)
        
        if type(items) is list:
            output = []
            for i,j in zip(items,routeselection):
                output.append(self._get_item(i,subjects,j))
        else:
            output = self._get_item(items,subjects,routeselection)
        return output
    
    def _get_item(self, item_name,query_subjects,routeselection):
  
        if routeselection == None:
            item_invindex = [k for k,inv in enumerate(self._inventory) \
                                            if item_name in inv[-1]]
            if len(item_invindex)>1:
                message = 'Multiple locations for item: '+item_name
                message+= '\nSelect Choices:'
                for i in item_invindex:
                    message+= '\n\t'+str(i)+' '+self._inventory[i][0]
                raise Exception(message)
                
            if len(item_invindex)==0:
                raise Exception('Unidentified item: '+item_name)
                
            item_invindex = item_invindex[0]
            
        else:
            item_invindex = routeselection
            if item_name not in self._inventory[item_invindex][-1]:
                raise Exception('Item: '+item_name+' not found in: '\
                                    +self._inventory[item_invindex][0])
                
                
                
        selected_node = self._inventory[item_invindex][1]
        
        node_subjects = getattr(selected_node,'Subjects')
        node_itemvalues = getattr(selected_node,item_name)
        
        try:
            if type(query_subjects) is list:
                subjects_sortorder = [node_subjects.index(k) \
                                        for k in query_subjects]    
                item_query = [node_itemvalues[k] for k in subjects_sortorder]  
            
            elif query_subjects == None :
                item_query = node_itemvalues
    
            else:
                subject_index = node_subjects.index(query_subjects)
                item_query = node_itemvalues[subject_index]
                
        except Exception as e:
            raise type(e)(e.message+'\nFor item: '+item_name+\
                           ' in location: '+self._inventory[item_invindex][0])
    
        return item_query
        
    @property
    def inventory(self):
        if hasattr(self,'_inventory'):
            print 'Item inventory:'
            for i,inv in enumerate(self._inventory):
                print '\t',i,inv[0],':',inv[-1] 
        else:
            print 'No inventory found'
    

class FolderNode(_Node):
    
    __handled_attributes = ['Folders','Subjects','Files']
    
    
    def __init__(self, node_dir, project_name,**kwargs):
        super(FolderNode,self).__init__(node_dir,project_name, 
                            hprops = self.__handled_attributes,**kwargs)
        
        # create folder nodes if folders exist in the node_info
        if 'Folders' in self._node_info.keys():
            self.__create_folders(project_name)
            
        if 'Files' in self._node_info.keys():
            self.__create_files()
            
        if 'Subjects' in self._node_info.keys():
            self._load_subjects()
                
    def __create_folders(self,project_name):
        
        subnodes = self._node_info['Folders']
        for subnode_name in subnodes.keys():
            subnode_dir = os.path.join(self._node_info['path'],subnode_name)
            try:
                self.__subnodes
            except AttributeError:
                self.__subnodes = []
                
            subnode = FolderNode(subnode_dir,project_name,
                                 node_info = subnodes[subnode_name])
            self.__subnodes.append(subnode)
            setattr(self,subnode_name,subnode)
            
            if hasattr(subnode,'_inventory'):
                try: 
                    self._inventory
                except AttributeError:
                    self._inventory = []
                
                for i in subnode._inventory:
                    if i[0] == None:
                        i[0] = subnode_name
                    else:
                        i[0] = subnode_name+'>'+i[0]
                
                self._inventory+=subnode._inventory

    
    def __create_files(self):
        subnodes = self._node_info['Files']
        for subnode_name in subnodes.keys():
            subnode_dir = self._node_info['path']
            try:
                self.__subnodes
            except AttributeError:
                self.__subnodes = []
            
            subnode = FileNode(subnode_dir,
                               node_info = subnodes[subnode_name])
            self.__subnodes.append(subnode)
            setattr(self,subnode_name,subnode)
            
            # merging intventories
            
            if hasattr(subnode,'_inventory'):
                try: 
                    self._inventory
                except AttributeError:
                    self._inventory = []
                
                for i in subnode._inventory:
                    if i[0] == None:
                        i[0] = subnode_name
                    else:
                        i[0] = subnode_name+'>'+i[0]
                
                self._inventory+=subnode._inventory

    
    

class FileNode(_Node):
    __handled_attributes = ['Subjects','FileName','Type','Items','Sheet']
    
#    @property
#    def hprops(self):
#        return self.__handled_attributes
    
    def __init__(self, node_dir, **kwargs):
        super(FileNode,self).__init__(node_dir,'NONE',
                                hprops = self.__handled_attributes,**kwargs)

        filepath = os.path.join(node_dir,self._node_info['FileName'])
        if os.path.isfile(filepath):
            self.__load_file(filepath,self._node_info)
            
    def __load_file(self,filepath,node_info):
        
        try:

            if node_info['Type'] == 'CSV':
                items_data = _load_csv(filepath)
                
            if node_info['Type'] == 'XLS':
                items_data = _load_xls(filepath,node_info['Sheet'])
                
            if node_info['Type'] == 'ListLines':
                items_data = _load_llines(filepath)
        
            
        except Exception as e:
            raise type(e)(e.message + '\n When loading data file : ' + filepath)
        
        if node_info['Type'] in ['CSV','XLS','ListLines']:
            if 'Items' not in node_info.keys():
                 node_info.update({'Items': items_data.keys()})
                 
            assert len(node_info['Items'])>0     
            
            if 'Subjects' in node_info.keys():
                if node_info['Subjects'] in node_info['Items']:
                    setattr(self,'Subjects',items_data[node_info['Subjects']])
                    node_info['Items'].remove(node_info['Subjects'])
                else:
                    self._load_subjects()
    
                assert len(self.Subjects) == len(items_data[items_data.keys()[0]])
                
                # creating inventory
                self._inventory =[[None,self,self._node_info.get('Items')]]
        
            for item in node_info['Items']:
                setattr(self,item,items_data[item])
        

        
def _load_csv(filepath):       
    csv_data = pandas.read_csv(filepath)
    
    items_data = dict([(item_name,list(csv_data.get(item_name))) \
                            for item_name in list(csv_data.columns)])
    return items_data
                 
                 
def _load_xls(filepath,sheet):
    xls_data = pandas.read_excel(filepath,sheet)
    items_data = dict([(item_name,list(xls_data.get(item_name))) \
                            for item_name in list(xls_data.columns)])
                                
    return items_data
    
    
def _load_llines(filepath):
    with open(filepath,'rt') as f:
        lines = f.readlines()
    lline_data = [eval(k) for k in lines]
    
    items_data = dict([(item_name,[k[i] for k in lline_data[1:]]) 
                                for i,item_name in enumerate(lline_data[0])])
                                    
    return items_data

        
#        

        

    
    
        
        
        
        
        
        