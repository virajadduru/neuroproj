# -*- coding: utf-8 -*-
"""
Created on Fri Feb 10 10:57:33 2017

Project : Grand-HeadCT

To get subject data: processed data, stats and subject info, from the project

@author: vradduru
"""
import os as os
import pandas as pandas

class GrandHeadCT(object):
    """
    available_groups : 'ALZ_CASE', 'ALZ_CTRL', 'AXIAL_89'
    """
    __available_items = []
    
    __available_groups = ['ALZ_CASE','ALZ_CTRL','AXIAL_89']
    __project_dir = r'E:\PROCESSED_DATA\HEADCT\Grand-headCT'
    
    @property
    def projectDir(self):
        return self.__project_dir
    
    @projectDir.setter
    def projectDir(self, path):
        assert os.path.isdir(path) == True
        self.__project_dir = path
        
    @property
    def available_groups(self):
        return self.__available_groups
    @property
    def available_items(self):
        return self.__available_items
    
    def __init__(self,group):
        assert group in self.__available_groups
        self.__subject_group = group
        
        self.__item_methods = [self.__getSubjectInfo,self.__getImageInfo,self.__getImgQual,self.__getTissueVols,self.__getTBVmanseg,self.__getSegQuality]
        
    @property
    def subjectGroup(self):
        return self.__subject_group
        
        
    @property
    def subjects(self):
        return self.__getSubjects()
        
    def inSubjects(self,query_subjects):
        
        if type(query_subjects) is list:
            return [i in self.subjects for i in query_subjects]
            
        else:
            return query_subjects in self.subjects
        
    
    def __getSubjects(self):
        
        try:
            self.__sub_list
        
        except AttributeError:
            sublist_filename = os.path.join(self.__project_dir,self.__subject_group,r'subjects_list.txt')
        
            with open(sublist_filename,'rt') as f:
                lines = f.readlines()
            self.__sub_list = [k.rstrip() for k in lines]
        
        return self.__sub_list
    
    def getSubjectsManseg(self):

        sublist_filename = os.path.join(self.__project_dir,self.__subject_group,r'subjects_list_manseg.txt')
    
        with open(sublist_filename,'rt') as f:
            lines = f.readlines()
        sub_list = [k.rstrip() for k in lines]
        
        return sub_list
    
    def getSubjectData(self, subjects, items,):
        """
        Subjects: Single subject or a list of subject names
        items:    Single item or a list of items
        """
        # If item is a single item just return the item value for the subjects 
        # returned by the function   
        group_folder = os.path.join(self.__project_dir,self.__subject_group)
        if type(items) is list:
            output = []
            for i in items:
                output.append(self.__getItem(subjects,i,group_folder))
        else:
            output = self.__getItem(subjects,items,group_folder)
        return output
        
    
                
    def __getItem(self,subjects,item_name,group_folder):
        list_index = [(ind,k.index(item_name)) for ind,k in enumerate(self.__available_items) if item_name in k]
        try:        
            assert len(list_index) == 1
        except AssertionError:
            print 'ERROR:', len(list_index), 'items found for item',item_name
            raise
            
        item_index = list_index[0][1]
        list_index = list_index[0][0]
        get_function = self.__item_methods[list_index]
        return get_function(query_subjects = subjects,item_index = item_index, item_name = item_name,group_folder = group_folder)
    
    

    # Extracts information from ALZ_HEADCT_SEND.xlsx file
    __available_items.append(['AGE_AT_CT','SEX','ALZ_(Y/N)','DM_(Y/N)'])
    
    def __getSubjectInfo(self,**kwargs):
        query_subjects = kwargs['query_subjects']
        item_name = kwargs['item_name']

        try:
            self.__diagnosis_data
        except AttributeError:
            subjectinfo_filename = os.path.join(self.__project_dir,'ALZ_HeadCT_SEND.xlsx')
            sheet_names = ['ALZ_CASE','ALZ_CONTROL','DM_CASE','DM_CONTROL']
            current_sheetname = sheet_names[self.__available_groups.index(self.subjectGroup)]
            self.__subjectinfo_data = pandas.read_excel(subjectinfo_filename, current_sheetname)
            
        
        
        queryitem_values = list(self.__subjectinfo_data.get(item_name))
        sessionIDs_subjectinfo = list(self.__subjectinfo_data.get('DE_ID_ACC_NUM'))
        
        
        if type(query_subjects) is list:
            querysubjects_sessionIDs = [k.split('_')[1] for k in query_subjects]
            subjects_sortorder = [sessionIDs_subjectinfo.index(k) for k in querysubjects_sessionIDs]    
            queryitem = [queryitem_values[k] for k in subjects_sortorder]  
        
        elif type(query_subjects) is str:
            querysubjects_sessionIDs = query_subjects.split('_')[1]
            subject_index = sessionIDs_subjectinfo.index(querysubjects_sessionIDs)
            queryitem = queryitem_values[subject_index]
            
        return queryitem
        
        
    # Get image_info from imageinfo.txt in data/images folder
    __available_items.append(['', 'PatientAge', 'PatientSex', 
                            'SeriesNumber', 'SeriesDescription','NumberofSlices',
                            'GantryDetectorTilt','PixelSpacing','SliceThickness',
                            'Manufacturer', 'ManufacturerModelName'])
    def __getImageInfo(self,**kwargs):
        query_subjects = kwargs['query_subjects']
        item_index = kwargs['item_index']
        group_folder = kwargs['group_folder']
        
        try:
            self.__image_data
        except AttributeError:
            imageinfo_filename = os.path.join(group_folder,'data','images','imageinfo.txt')
            with open(imageinfo_filename,'rt') as f:
                lines = f.readlines()
            self.__image_data = [eval(k) for k in lines[1:]]
            
        subjects_imageinfo = [k[0] for k in self.__image_data]    
        
        if type(query_subjects) is list:
            subjects_sortorder = [subjects_imageinfo.index(k) for k in query_subjects]    
            item_query = [self.__image_data[k][item_index] for k in subjects_sortorder]  
        else:
            subject_index = subjects_imageinfo.index(query_subjects)
            item_query = self.__image_data[subject_index][item_index]
            
        return item_query

    
    

    
    __available_items.append(['Image_accepted'])
    def __getImgQual(self,**kwargs):
        query_subjects = kwargs['query_subjects']
        group_folder = kwargs['group_folder']
        item_name = kwargs['item_name']
    
        try:
            self.__imgqual_data
        except AttributeError:
            imgqual_filename = os.path.join(group_folder,'data','ImageQuality.xlsx')
            self.__imgqual_data = pandas.read_excel(imgqual_filename, 'Sheet1')
            

        item_query = list(self.__imgqual_data.get(item_name))
        subjects_imgqual = list(self.__imgqual_data.Subject)
        
        if type(query_subjects) is list:
            subjects_sortorder = [subjects_imgqual.index(k) for k in query_subjects]    
            item_query = [item_query[k] for k in subjects_sortorder]  
        
        elif type(query_subjects) is str:
            subject_index = subjects_imgqual.index(query_subjects)
            item_query = item_query[subject_index]
            
        return item_query
        
    __available_items.append(['TIV','TBV'])
    def __getTissueVols(self,**kwargs):
        query_subjects = kwargs['query_subjects']
        group_folder = kwargs['group_folder']
        item_name = kwargs['item_name']
    
        try:
            self.__TBV_data
        except AttributeError:
            TBV_filename = os.path.join(group_folder,'SPM_flirt','output','TissueVols.csv')
            self.__TBV_data = pandas.read_csv(TBV_filename)

        item_query = list(self.__TBV_data.get(item_name))
        subjects_vol = list(self.__TBV_data.Subjects)
        
        if type(query_subjects) is list:
            subjects_sortorder = [subjects_vol.index(k) for k in query_subjects]    
            item_query = [item_query[k] for k in subjects_sortorder]  
        
        elif type(query_subjects) is str:
            subject_index = subjects_vol.index(query_subjects)
            item_query = item_query[subject_index]
            
        return item_query
        
    __available_items.append(['TBV_manseg'])
    def __getTBVmanseg(self,**kwargs):
        query_subjects = kwargs['query_subjects']
        group_folder = kwargs['group_folder']
        item_name = kwargs['item_name']
    
        try:
            self.__TBVManSeg_data
        except AttributeError:
            TBV_filename = os.path.join(group_folder,'MANSEG_data','output','TBV.csv')
            self.__TBVManSeg_data = pandas.read_csv(TBV_filename)

        item_query = list(self.__TBVManSeg_data.get(item_name))
        subjects_TBV = list(self.__TBVManSeg_data.Subject)
        
        if type(query_subjects) is list:
            subjects_sortorder = [subjects_TBV.index(k) for k in query_subjects]    
            item_query = [item_query[k] for k in subjects_sortorder]  
        
        elif type(query_subjects) is str:
            subject_index = subjects_TBV.index(query_subjects)
            item_query = item_query[subject_index]
            
        return item_query
        
        
    __available_items.append(['TBVSEG_accepted','TIVSEG_accepted'])
    def __getSegQuality(self,**kwargs):
        query_subjects = kwargs['query_subjects']
        group_folder = kwargs['group_folder']
        item_name = kwargs['item_name']
    
        try:
            self.__segqual_data
        except AttributeError:
            segqual_filename = os.path.join(group_folder,'SPM_flirt','output','SEG_qualitycheck.xlsx')
            self.__segqual_data = pandas.read_excel(segqual_filename, 'Sheet1')
            

        item_query = list(self.__segqual_data.get(item_name))
        subjects_segqual = list(self.__segqual_data.Subject)
        
        if type(query_subjects) is list:
            subjects_sortorder = [subjects_segqual.index(k) for k in query_subjects]    
            item_query = [item_query[k] for k in subjects_sortorder]  
        
        elif type(query_subjects) is str:
            subject_index = subjects_segqual.index(query_subjects)
            item_query = item_query[subject_index]
            
        return item_query
        
        
        